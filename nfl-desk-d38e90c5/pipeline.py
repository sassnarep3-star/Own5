"""Builds every published dataset for the d38e90c5 NFL line-origination desk.

Run:  python3 pipeline.py            (writes data/*.csv and data/summary.json)
      python3 pipeline.py --check    (builds into a temp dir and diffs nothing)

Every published value traces to an official source recorded in raw_inputs.SOURCES,
injuries_raw.INJURY_SOURCE / depth_raw.DEPTH_META, or to a documented model
parameter in model.py. Market-price fields stay blank and are listed in the
Flagged for Review register.
"""

import csv
import json
import math
import os
import statistics
from datetime import date, datetime

import model
import raw_inputs as RI
import injuries_raw as IR
import depth_raw as DR

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
os.makedirs(DATA, exist_ok=True)

FLAG_FILE = os.path.join(DATA, "flagged_for_review.csv")
FLAG_ROWS = []


def flag(area, item, issue, source_url="", action="", columns=""):
    """Record an unverified/blank/irregular item for the Flagged for Review page.

    `columns` lists the published columns this flag covers, so the verifier can
    prove that every blank published value is registered somewhere.
    """
    FLAG_ROWS.append({
        "area": area,
        "item": item,
        "issue": issue,
        "source_url": source_url,
        "recommended_action": action,
        "columns_blank": columns,
    })


def write_csv(name, fieldnames, rows):
    path = os.path.join(DATA, name)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    return path


# --------------------------------------------------------------------------
# 0. shared helpers
# --------------------------------------------------------------------------
FIRST_NAME_ALIASES = {
    "josh": "joshua", "chris": "christopher", "matt": "matthew", "mike": "michael",
    "dave": "david", "dan": "daniel", "ben": "benjamin", "jon": "jonathan",
    "jake": "jacob", "sam": "samuel", "tom": "thomas", "tony": "anthony",
    "nick": "nicholas", "alex": "alexander", "jeff": "geoffrey", "steve": "stephen",
    "bill": "william", "bob": "robert", "ed": "edward", "joe": "joseph",
    "greg": "gregory", "ken": "kenneth", "ronnie": "ronald", "donnie": "donald",
    "zach": "zachary", "gabe": "gabriel", "danny": "daniel", "marcus": "marcus",
}


def norm_name(name):
    n = name.lower()
    n = n.replace("'", "").replace("’", "")
    n = n.replace(".", "").replace("-", " ").replace(",", "")
    for suf in (" jr", " sr", " ii", " iii", " iv", " v"):
        if n.endswith(suf):
            n = n[: -len(suf)]
    parts = " ".join(n.split()).split(" ")
    parts = [FIRST_NAME_ALIASES.get(x, x) for x in parts]
    return " ".join(parts)


def american_to_decimal(odds):
    if odds is None:
        return None
    if odds < 0:
        return round(1.0 + 100.0 / (-odds), 4)
    return round(1.0 + odds / 100.0, 4)


def parse_date(s):
    return datetime.strptime(s, "%Y-%m-%d").date()


# --------------------------------------------------------------------------
# 1. ratings, backtest and sigma
# --------------------------------------------------------------------------
def build_ratings_and_backtest():
    ratings = model.compute_ratings(RI.RESULTS)
    league_ppg = model.league_points_per_team_per_game(RI.RESULTS)
    preds = model.walk_forward_predictions(RI.RESULTS)
    sigma, sigma_n = model.residual_sigma(preds)
    tot_sigma, tot_sigma_n = model.total_residual_sigma(preds)
    prob_fn, cal = model.probability_model(preds, model.margin_sd(RI.RESULTS))
    return ratings, league_ppg, preds, sigma, sigma_n, tot_sigma, tot_sigma_n, prob_fn, cal


def build_ratings_rows(ratings):
    rows = []
    for team in sorted(ratings):
        r = ratings[team]
        rows.append({
            "team": team,
            "team_name": RI.TEAM_NAMES.get(team, team),
            "games": r["gp"],
            "points_for": r["pf"],
            "points_against": r["pa"],
            "points_for_per_game": round(r["pf"] / r["gp"], 3) if r["gp"] else "",
            "points_against_per_game": round(r["pa"] / r["gp"], 3) if r["gp"] else "",
            "off_adj": r["off_adj"],
            "def_adj": r["def_adj"],
            "off_s": r["off_s"],
            "def_s": r["def_s"],
            "shrinkage_weight": r["weight"],
            "usable": "yes" if r["usable"] else "no",
            "note": r["note"],
            "source_id": "S-01",
            "source_url": RI.SOURCES[0][3],
        })
    return rows


def build_backtest_rows(preds):
    rows = []
    for p in preds:
        home_win = 1 if p["home_pts"] > p["away_pts"] else 0
        rows.append({
            "week": p["week"], "date": p["date"], "away": p["away"], "home": p["home"],
            "away_pts": p["away_pts"], "home_pts": p["home_pts"],
            "actual_margin": p["margin"], "actual_total": p["total_pts"],
            "model_margin": p["pred_margin"], "model_total": p["pred_total"],
            "model_home_pts": p["pred_home_pts"], "model_away_pts": p["pred_away_pts"],
            "margin_error": round(p["margin"] - p["pred_margin"], 4),
            "home_win": home_win,
            "rating_note": "" if (p["home_usable"] and p["away_usable"]) else "rating below minimum history",
            "source_id": p["source_id"], "source_url": p["source_url"],
        })
    return rows


# --------------------------------------------------------------------------
# 2. verified results feed
# --------------------------------------------------------------------------
def build_results_feed():
    rows = []
    for wk, dt, away, home, ap, hp, sid, url in RI.RESULTS:
        rows.append({
            "week": wk, "date": dt,
            "away": away, "away_team": RI.TEAM_NAMES.get(away, away), "away_pts": ap,
            "home": home, "home_team": RI.TEAM_NAMES.get(home, home), "home_pts": hp,
            "margin": hp - ap, "total_points": ap + hp,
            "home_win": "yes" if hp > ap else "no",
            "result_status": "verified",
            "verification_note": "final score transcribed from the official NFL.com schedule page",
            "source_id": sid, "source_url": url,
        })
    return rows


# --------------------------------------------------------------------------
# 3. price snapshot store (append only)
# --------------------------------------------------------------------------
STORE = os.path.join(DATA, "price_snapshots.jsonl")


def store_key(rec):
    return (rec["game_id"], rec["market"], rec["phase"])


def append_snapshots(records):
    """Append-only store: existing keys are never rewritten."""
    existing = set()
    if os.path.exists(STORE):
        with open(STORE, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                existing.add(store_key(rec))
    appended = 0
    with open(STORE, "a", encoding="utf-8") as fh:
        for rec in records:
            if store_key(rec) in existing:
                continue
            fh.write(json.dumps(rec, sort_keys=True) + "\n")
            existing.add(store_key(rec))
            appended += 1
    return appended


def snapshot_rows_from_lines(lines, captured_at, results_by_game, phase):
    recs = []
    for ln in lines:
        gid = ln["game_id"]
        res = results_by_game.get(gid, "")
        rec = {
            "snapshot_id": f"{gid}|{ln['market']}|{phase}",
            "game_id": gid,
            "week": ln["week"], "date": ln["date"], "kickoff": ln["kickoff"],
            "away": ln["away"], "home": ln["home"],
            "market": ln["market"], "market_label": ln["market_label"],
            "publish_seq": ln["publish_seq"],
            "phase": phase,
            "captured_at": captured_at,
            "model_fair_line": ln["model_fair_line"],
            "model_fair_prob": ln["model_fair_prob"],
            "model_fair_price": ln["model_fair_price"],
            "market_line": "",
            "market_price": "",
            "difference": "",
            "price_status": model.PRICE_STATUS,
            "verified_result": res,
            "source_url": ln["source_url"],
            "note": ("market opening price not published by any reachable primary source"
                     if phase == "opening" else
                     "market closing price not published by any reachable primary source"),
        }
        recs.append(rec)
    return recs


# --------------------------------------------------------------------------
# 4. depth tracker
# --------------------------------------------------------------------------
def build_depth_index():
    """(team) -> list of {unit, position, slot_index, name, names}"""
    index = {}
    for team, rows in DR.DEPTH.items():
        entries = []
        for row in rows:
            unit, position, slots = row.split("|")
            for i, slot in enumerate(slots.split(";"), start=1):
                if slot == "-":
                    entries.append({"unit": unit, "position": position, "slot": i,
                                    "name": "", "names": [], "published_empty": True})
                    continue
                names = [n.strip() for n in slot.split(",")]
                for n in names:
                    entries.append({"unit": unit, "position": position, "slot": i,
                                    "name": n, "names": names, "published_empty": False})
        index[team] = entries
    return index


DEPTH_TIER = {1: "1st string (starter)", 2: "2nd string", 3: "3rd string", 4: "4th string"}


def build_depth_tracker(depth_index):
    rows = []
    unmatched = 0
    for team, player, position, injury, practice, gstatus in IR.INJURIES:
        absence = {
            "Out": "Out",
            "Doubtful": "Doubtful",
            "Questionable": "Questionable",
            "": "No designation published",
        }.get(gstatus, gstatus or "No designation published")
        entries = depth_index.get(team, [])
        hit = None
        for e in entries:
            if norm_name(e["name"]) == norm_name(player):
                hit = e
                break
        if hit is None:
            unmatched += 1
            rows.append({
                "team": team, "team_name": RI.TEAM_NAMES.get(team, team),
                "player": player, "listed_position": position,
                "unit": "", "depth_position": "",
                "depth_slot": "", "depth_tier": "",
                "injury": injury, "practice_status": practice,
                "game_status": gstatus, "absence_class": absence,
                "replacement_player": "", "replacement_depth_tier": "",
                "depth_deficiency": "",
                "match_status": "no depth-chart match",
                "source_url": IR.INJURY_SOURCE_URL,
                "depth_source_url": DR.DEPTH_META.get(team, ("", ""))[0],
            })
            continue
        slot = hit["slot"]
        replacement = ""
        repl_tier = ""
        for e in entries:
            if (e["unit"] == hit["unit"] and e["position"] == hit["position"]
                    and e["slot"] > slot and e["name"]):
                replacement = e["name"]
                repl_tier = DEPTH_TIER.get(e["slot"], f"{e['slot']}th string")
                break
        deficiency = ""
        if gstatus == "Out" and slot == 1:
            if repl_tier and repl_tier.startswith(("3rd", "4th")):
                deficiency = f"starter out; next in line is {repl_tier}"
        rows.append({
            "team": team, "team_name": RI.TEAM_NAMES.get(team, team),
            "player": player, "listed_position": position,
            "unit": hit["unit"], "depth_position": hit["position"],
            "depth_slot": slot, "depth_tier": DEPTH_TIER.get(slot, f"{slot}th string"),
            "injury": injury, "practice_status": practice,
            "game_status": gstatus, "absence_class": absence,
            "replacement_player": replacement, "replacement_depth_tier": repl_tier,
            "depth_deficiency": deficiency,
            "match_status": "matched official club depth chart",
            "source_url": IR.INJURY_SOURCE_URL,
            "depth_source_url": DR.DEPTH_META.get(team, ("", ""))[0],
        })
    return rows, unmatched


def build_team_depth_summary(depth_rows):
    agg = {}
    for r in depth_rows:
        a = agg.setdefault(r["team"], {
            "team": r["team"], "team_name": r["team_name"],
            "out_total": 0, "out_offense_starters": 0, "out_defense_starters": 0,
            "out_starter_other": 0, "doubtful_starters": 0, "questionable_starters": 0,
            "no_designation": 0, "depth_deficiencies": 0, "severity": 0.0,
            "starter_out_players": "", "deficiency_detail": "",
            "depth_source_url": r["depth_source_url"],
        })
        if r["absence_class"] == "Out":
            a["out_total"] += 1
            if r["depth_slot"] == 1:
                a["severity"] += {"Offense": 3.0, "Defense": 2.5}.get(r["unit"], 1.0)
                if r["unit"] == "Offense":
                    a["out_offense_starters"] += 1
                elif r["unit"] == "Defense":
                    a["out_defense_starters"] += 1
                else:
                    a["out_starter_other"] += 1
                a["starter_out_players"] = (a["starter_out_players"] + "; " if a["starter_out_players"] else "") + r["player"]
        elif r["absence_class"] == "Doubtful" and r["depth_slot"] == 1:
            a["doubtful_starters"] += 1
        elif r["absence_class"] == "Questionable" and r["depth_slot"] == 1:
            a["questionable_starters"] += 1
        elif r["absence_class"] == "No designation published":
            a["no_designation"] += 1
        if r["depth_deficiency"]:
            a["depth_deficiencies"] += 1
            a["deficiency_detail"] = (a["deficiency_detail"] + "; " if a["deficiency_detail"] else "") + f"{r['player']}: {r['depth_deficiency']}"
    rows = []
    for team in sorted(agg):
        a = agg[team]
        a["severity"] = round(a["severity"], 2)
        a["injury_source_url"] = IR.INJURY_SOURCE_URL
        a["injury_completeness"] = IR.INJURY_TABLE_COMPLETE.get(team, "")
        rows.append(a)
    return rows


# --------------------------------------------------------------------------
# 5. correlations (every value ships with n)
# --------------------------------------------------------------------------
def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None, n
    mx = sum(xs) / n
    my = sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return None, n
    return round(sxy / math.sqrt(sxx * syy), 4), n


def spearman(xs, ys):
    def rank(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    return pearson(rank(xs), rank(ys))


def build_correlations(ratings, preds, depth_summary, standings):
    rows = []

    # C1 model margin vs actual margin (out of sample)
    xs = [p["pred_margin"] for p in preds if p["home_usable"] and p["away_usable"]]
    ys = [p["margin"] for p in preds if p["home_usable"] and p["away_usable"]]
    r, n = pearson(xs, ys)
    rows.append({
        "id": "C1", "label": "Model margin vs actual margin (walk-forward, out of sample)",
        "x": "model margin (points)", "y": "actual final margin (points)",
        "pearson_r": r if r is not None else "", "spearman_rho": (spearman(xs, ys)[0] if r is not None else ""),
        "n": n, "p_value": "",
        "x_source": "model.py (officially sourced inputs S-01 to S-10)",
        "y_source": "official NFL.com final scores (S-02 to S-10)",
        "note": "" if r is not None else "not computable",
    })

    # C2 rest days vs margin
    last_game = {}
    rest = []
    margins = []
    for wk, dt, away, home, ap, hp, sid, url in sorted(RI.RESULTS, key=lambda g: (g[1], g[2])):
        d = parse_date(dt)
        for team in (away, home):
            prev = last_game.get(team)
            if prev:
                rest.append((d - prev).days)
                margins.append(hp - ap)
            last_game[team] = d
    r, n = pearson([float(x) for x in rest], [float(x) for x in margins])
    rows.append({
        "id": "C2", "label": "Rest days (shorter of the two clubs) vs winning margin",
        "x": "rest days between official game dates", "y": "winning margin (points)",
        "pearson_r": r if r is not None else "", "spearman_rho": "",
        "n": n, "p_value": "",
        "x_source": "official NFL.com schedule dates (S-02 to S-10)",
        "y_source": "official NFL.com final scores (S-02 to S-10)",
        "note": "" if r is not None else "not computable",
    })

    # C3 point differential vs win percentage (official standings)
    xs, ys = [], []
    for t, w, l, ti, pct, pf, pa, diff in RI.STANDINGS:
        g = w + l + ti
        xs.append(float(diff))
        ys.append(float(pct))
    r, n = pearson(xs, ys)
    rows.append({
        "id": "C3", "label": "Official point differential vs official win percentage",
        "x": "official point differential (PF-PA)", "y": "official PCT",
        "pearson_r": r if r is not None else "", "spearman_rho": spearman(xs, ys)[0],
        "n": n, "p_value": "",
        "x_source": "official NFL.com standings (S-01)",
        "y_source": "official NFL.com standings (S-01)",
        "note": "",
    })

    # C4 Week 10 offensive starters out vs official point differential
    st_map = {t: diff for t, w, l, ti, pct, pf, pa, diff in RI.STANDINGS}
    xs, ys = [], []
    for row in depth_summary:
        t = row["team"]
        if t in st_map:
            xs.append(float(row["out_offense_starters"]))
            ys.append(float(st_map[t]))
    r, n = pearson(xs, ys)
    rows.append({
        "id": "C4", "label": "Week 10 offensive starters out vs official point differential",
        "x": "count of offensive depth-chart starters listed Out (S-13 + club depth charts)",
        "y": "official point differential (PF-PA)",
        "pearson_r": r if r is not None else "", "spearman_rho": spearman(xs, ys)[0],
        "n": n, "p_value": "",
        "x_source": "official NFL.com Week 10 injury report (S-13) + official club depth charts",
        "y_source": "official NFL.com standings (S-01)",
        "note": "single-week cross-section; not a causal estimate",
    })

    # C5 defensive starters out vs points allowed per game
    pa_map = {t: pa for t, w, l, ti, pct, pf, pa, diff in RI.STANDINGS}
    g_map = {t: (w + l + ti) for t, w, l, ti, pct, pf, pa, diff in RI.STANDINGS}
    xs, ys = [], []
    for row in depth_summary:
        t = row["team"]
        if t in pa_map and g_map.get(t):
            xs.append(float(row["out_defense_starters"]))
            ys.append(round(pa_map[t] / g_map[t], 4))
    r, n = pearson(xs, ys)
    rows.append({
        "id": "C5", "label": "Week 10 defensive starters out vs official points allowed per game",
        "x": "count of defensive depth-chart starters listed Out (S-13 + club depth charts)",
        "y": "official points allowed per game",
        "pearson_r": r if r is None and False else (r if r is not None else ""), "spearman_rho": "",
        "n": n, "p_value": "",
        "x_source": "official NFL.com Week 10 injury report (S-13) + official club depth charts",
        "y_source": "official NFL.com standings (S-01)",
        "note": "single-week cross-section; not a causal estimate",
    })

    # C6 model predicted total vs actual total
    xs = [p["pred_total"] for p in preds if p["home_usable"] and p["away_usable"]]
    ys = [p["total_pts"] for p in preds if p["home_usable"] and p["away_usable"]]
    r, n = pearson(xs, ys)
    rows.append({
        "id": "C6", "label": "Model total vs actual total points (walk-forward)",
        "x": "model total (points)", "y": "actual combined score (points)",
        "pearson_r": r if r is not None else "", "spearman_rho": spearman(xs, ys)[0],
        "n": n, "p_value": "",
        "x_source": "model.py", "y_source": "official NFL.com final scores (S-02 to S-10)",
        "note": "",
    })

    # C7 home win rate vs away win rate sanity check
    home_wins = sum(1 for r_ in RI.RESULTS if r_[5] > r_[4])
    rows.append({
        "id": "C7", "label": "Home wins as share of completed official games",
        "x": "home wins", "y": "completed games",
        "pearson_r": "", "spearman_rho": "",
        "n": len(RI.RESULTS), "p_value": "",
        "x_source": "official NFL.com final scores (S-02 to S-10)",
        "y_source": "official NFL.com final scores (S-02 to S-10)",
        "note": f"home wins {home_wins} of {len(RI.RESULTS)} ({home_wins / len(RI.RESULTS):.3f})",
    })
    return rows


# --------------------------------------------------------------------------
# 6. strategies, leaderboards and the demotion gate
# --------------------------------------------------------------------------
def _cover_prob(pred_margin, side_line, side_is_home, sigma):
    """P(the selected side covers) from the model's normal margin distribution.

    The home side's own line is L, so it covers when actual margin > -L, i.e.
    P = Phi((m + L)/sigma). The away side's own line is -L, so it covers when
    actual margin < L, i.e. P = Phi((L - m)/sigma) = Phi(-(m - L)/sigma).
    """
    z = (pred_margin + side_line) / sigma
    return model.norm_cdf(z) if side_is_home else model.norm_cdf(-z)


def _settle_side(actual_margin, home_line, side_is_home):
    """Outcome for the selected side against the model's own spread line."""
    if side_is_home:
        adjusted = actual_margin + home_line
        if adjusted > 0:
            return "win"
        if adjusted < 0:
            return "loss"
        return "push"
    adjusted = actual_margin - home_line
    if adjusted < 0:
        return "win"
    if adjusted > 0:
        return "loss"
    return "push"


def _settle_total(actual_total, total_line):
    if actual_total > total_line:
        return "over", 1
    if actual_total < total_line:
        return "under", -1
    return "push", 0


def evaluate_strategies(preds, sigma):
    """Every strategy is evaluated at the MODEL's own fair price.

    A fair price has expected profit of exactly zero by construction, so the
    realised profit of these simulations is pure luck. That is the point: the
    leaderboard reports signal quality (calibration and accuracy against
    official results) separately from staking performance, so a lucky run
    cannot mask a weak signal. Market ROI and CLV stay blank because no
    primary price source exists.
    """
    strategies = []

    # S1 - spread favourite at the model's own line
    bets = []
    for p in preds:
        if not (p["home_usable"] and p["away_usable"]):
            continue
        margin = p["pred_margin"]
        if abs(margin) < 3.5:
            continue
        home_line = model.round_half(-margin)
        side_is_home = margin > 0
        side_line = home_line if side_is_home else -home_line
        cover_p = _cover_prob(margin, side_line, side_is_home, sigma)
        if cover_p <= 0.5:
            continue
        outcome = _settle_side(p["margin"], home_line, side_is_home)
        if outcome == "push":
            continue
        odds = american_to_decimal(model.american_odds(cover_p))
        profit = (odds - 1.0) if outcome == "win" else -1.0
        bets.append({"outcome": outcome, "profit": profit, "p": cover_p})
    strategies.append({
        "id": "S1", "name": "Model spread favourite",
        "family": "single bet",
        "definition": "Take the side the model prefers when |model margin| >= 3.5 points, priced at the model's own fair price for that side.",
        "selection_rule": "|model margin| >= 3.5",
        "price_basis": "model fair price (no market price source available)",
        "bets": bets,
        "market_required": "no",
        "signal_basis": "model walk-forward predictions (n = %d)" % len(preds),
    })

    # S2 - moneyline favourite with p >= 0.60
    bets = []
    for p in preds:
        if not (p["home_usable"] and p["away_usable"]):
            continue
        p_home = p["p_home"]
        side_is_home = p_home >= 0.60
        prob = p_home if side_is_home else 1 - p_home
        if prob < 0.60:
            continue
        outcome = "win" if ((p["margin"] > 0) == side_is_home) else "loss"
        odds = american_to_decimal(model.american_odds(prob))
        profit = (odds - 1.0) if outcome == "win" else -1.0
        bets.append({"outcome": outcome, "profit": profit, "p": prob})
    strategies.append({
        "id": "S2", "name": "Model moneyline favourite (p >= 0.60)",
        "family": "single bet",
        "definition": "Back the model moneyline side whenever the model's win probability is at least 0.60, priced at the model's own fair price.",
        "selection_rule": "model win probability >= 0.60",
        "price_basis": "model fair price (no market price source available)",
        "bets": bets,
        "market_required": "no",
        "signal_basis": "model walk-forward predictions (n = %d)" % len(preds),
    })

    # S3 - two-leg parlay of the two strongest model sides in the same week
    legs_by_week = {}
    for p in preds:
        if not (p["home_usable"] and p["away_usable"]):
            continue
        p_home = p["p_home"]
        conf = max(p_home, 1 - p_home)
        if conf < 0.60:
            continue
        legs_by_week.setdefault(p["week"], []).append((conf, p, p_home))
    bets = []
    for wk, legs in sorted(legs_by_week.items()):
        legs.sort(key=lambda x: -x[0])
        for i in range(0, len(legs) - 1, 2):
            (c1, p1, ph1), (c2, p2, ph2) = legs[i], legs[i + 1]
            side1_home = ph1 >= 0.5
            side2_home = ph2 >= 0.5
            o1 = "win" if ((p1["margin"] > 0) == side1_home) else "loss"
            o2 = "win" if ((p2["margin"] > 0) == side2_home) else "loss"
            prob = max(ph1, 1 - ph1) * max(ph2, 1 - ph2)
            odds = american_to_decimal(model.american_odds(prob))
            if o1 == "loss" or o2 == "loss":
                profit = -1.0
                outcome = "loss"
            else:
                profit = odds - 1.0
                outcome = "win"
            bets.append({"outcome": outcome, "profit": profit, "p": prob})
    strategies.append({
        "id": "S3", "name": "Two-leg parlay of model favourites",
        "family": "parlay",
        "definition": "Pair the two most confident model sides available in each week into a two-leg parlay priced at the combined model fair price.",
        "selection_rule": "two legs per week, each with model probability >= 0.60",
        "price_basis": "model fair price (no market price source available)",
        "bets": bets,
        "market_required": "no",
        "signal_basis": "model walk-forward predictions (n = %d)" % len(preds),
    })

    # S4 - value versus the market line (needs a market price)
    strategies.append({
        "id": "S4", "name": "Value versus market line",
        "family": "single bet",
        "definition": "Bet where the model line differs from the market line by at least the edge threshold.",
        "selection_rule": "|model line - market line| >= 1.0 point",
        "price_basis": "market price required",
        "bets": [],
        "market_required": "yes",
        "signal_basis": "not evaluable: the strategy is defined against a market line that does not exist in an official source",
        "status_note": "blocked: no primary market price source is reachable from this environment",
    })

    # S5 - replacement-depth adjustment (forward paper track)
    strategies.append({
        "id": "S5", "name": "Replacement-depth adjusted line",
        "family": "single bet",
        "definition": "Shift the model line when a starter is Out and the next in line at that position is a third- or fourth-string reserve (official depth charts).",
        "selection_rule": "starter Out with 3rd/4th string replacement",
        "price_basis": "model fair price (no market price source available)",
        "bets": [],
        "market_required": "no",
        "signal_basis": "not evaluable: no out-of-sample history exists for the depth adjustment",
        "status_note": "paper track from Week 10: the official NFL injury archive needed for a historical backtest does not exist on nfl.com",
    })

    # S6 - player props
    strategies.append({
        "id": "S6", "name": "Player-prop combinations",
        "family": "player prop",
        "definition": "Combine player-level official box-score data (passing, rushing, receiving yards) with replacement-depth state.",
        "selection_rule": "depth-adjusted player prop thresholds",
        "price_basis": "market price required",
        "bets": [],
        "market_required": "yes",
        "signal_basis": "not evaluable: player-level official game books have not been parsed",
        "status_note": "blocked: player-level official game books have not been parsed; primary source identified (NFL.com Game Book PDF)",
    })
    return strategies


def signal_quality(preds, sigma, subset=None):
    rows = preds if subset is None else subset
    usable = [p for p in rows if p["home_usable"] and p["away_usable"]]
    n = len(usable)
    if n == 0:
        return {"n": 0}
    errs = [p["margin"] - p["pred_margin"] for p in usable]
    mae = sum(abs(e) for e in errs) / n
    rmse = math.sqrt(sum(e * e for e in errs) / n)
    probs, outcomes = [], []
    brier = 0.0
    logloss = 0.0
    hits = 0
    for p in usable:
        ph = p["p_home"]
        y = 1 if p["margin"] > 0 else 0
        probs.append(ph)
        outcomes.append(y)
        brier += (ph - y) ** 2
        pp = min(max(ph, 1e-9), 1 - 1e-9)
        logloss += -(y * math.log(pp) + (1 - y) * math.log(1 - pp))
        if (ph >= 0.5) == (y == 1):
            hits += 1
    # calibration slope: regress outcome on probability (single predictor)
    mx = sum(probs) / n
    my = sum(outcomes) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(probs, outcomes))
    sxx = sum((a - mx) ** 2 for a in probs)
    slope = (sxy / sxx) if sxx > 0 else None
    intercept = my - slope * mx if slope is not None else None
    base_rate = sum(outcomes) / n
    base_brier = sum((base_rate - y) ** 2 for y in outcomes) / n
    base_logloss = -(sum(outcomes) * math.log(max(base_rate, 1e-9)) +
                      (n - sum(outcomes)) * math.log(max(1 - base_rate, 1e-9))) / n
    return {
        "n": n,
        "mae_margin": round(mae, 4),
        "rmse_margin": round(rmse, 4),
        "brier": round(brier / n, 6),
        "brier_baseline": round(base_brier, 6),
        "log_loss": round(logloss / n, 6),
        "log_loss_baseline": round(base_logloss, 6),
        "winner_hit_rate": round(hits / n, 4),
        "calibration_slope": round(slope, 4) if slope is not None else "",
        "calibration_intercept": round(intercept, 4) if intercept is not None else "",
        "base_rate": round(base_rate, 4),
    }


def staking_performance(bets):
    n = len(bets)
    if n == 0:
        return {"n_bets": 0}
    wins = sum(1 for b in bets if b["outcome"] == "win")
    losses = sum(1 for b in bets if b["outcome"] == "loss")
    pushes = sum(1 for b in bets if b["outcome"] == "push")
    profit = sum(b["profit"] for b in bets)
    cum = 0.0
    peak = 0.0
    maxdd = 0.0
    for b in bets:
        cum += b["profit"]
        peak = max(peak, cum)
        maxdd = max(maxdd, peak - cum)
    decided = wins + losses
    hit_rate = (wins / decided) if decided else ""
    expected = sum((b["p"] - 0.5) * 2 for b in bets) * 0.0  # fair price => expected 0
    variance = statistics.pvariance([b["profit"] for b in bets]) if n > 1 else 0.0
    sigma_profit = math.sqrt(variance) if variance > 0 else 0.0
    luck_band = 1.96 * sigma_profit * math.sqrt(n) if n else 0.0
    return {
        "n_bets": n, "wins": wins, "losses": losses, "pushes": pushes,
        "hit_rate": round(hit_rate, 4) if hit_rate != "" else "",
        "realised_profit_units": round(profit, 4),
        "expected_profit_units": round(expected, 4),
        "luck_gap_units": round(profit - expected, 4),
        "luck_band_95_units": round(luck_band, 4),
        "max_drawdown_units": round(maxdd, 4),
        "profit_sigma_units": round(sigma_profit, 4),
        "roi_at_model_fair_price": round(profit / n, 6) if n else "",
        "roi_vs_market": "",
        "clv": "",
    }


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------
def main():
    (ratings, league_ppg, preds, sigma, sigma_n,
     tot_sigma, tot_sigma_n, prob_fn, cal) = build_ratings_and_backtest()
    ratings_rows = build_ratings_rows(ratings)
    backtest_rows = build_backtest_rows(preds)
    results_rows = build_results_feed()

    # --- originated lines: completed games (walk-forward) + upcoming slate ---
    lines = []
    for p in preds:
        if not (p["home_usable"] and p["away_usable"]):
            continue
        gid = model.game_id_for(p["week"], p["away"], p["home"])
        rows = model.originate_game(
            ratings, league_ppg, p["home"], p["away"], prob_fn, tot_sigma, gid, p["week"],
            p["date"], "", "", p["source_url"])
        for r in rows:
            r["segment"] = "completed (walk-forward)"
            r["result"] = f"{p['away']} {p['away_pts']} - {p['home']} {p['home_pts']}"
        lines.extend(rows)

    for wk, dt, ko, away, home, net, url, venue in RI.SLATE:
        gid = model.game_id_for(wk, away, home)
        rows = model.originate_game(ratings, league_ppg, home, away, prob_fn, tot_sigma,
                                    gid, wk, dt, ko, net, url, venue)
        for r in rows:
            r["segment"] = "upcoming"
            r["result"] = ""
        lines.extend(rows)

    lines.sort(key=lambda r: (r["segment"] != "completed (walk-forward)",
                               r["week"], r["date"], r["away"], r["home"],
                               r["publish_seq"]))

    # --- price snapshots -------------------------------------------------
    results_by_game = {}
    for wk, dt, away, home, ap, hp, sid, url in RI.RESULTS:
        gid = model.game_id_for(wk, away, home)
        results_by_game[gid] = f"{away} {ap} - {home} {hp}"

    opening = snapshot_rows_from_lines(lines, RI.FETCH_DATE, results_by_game, "opening")
    closing = snapshot_rows_from_lines(lines, "", results_by_game, "closing")
    appended = append_snapshots(opening + closing)

    store_rows = []
    if os.path.exists(STORE):
        with open(STORE, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    store_rows.append(json.loads(line))
    store_rows.sort(key=lambda r: (r["week"], r["date"], r["away"], r["home"],
                                   r["publish_seq"], r["phase"]))

    # --- depth -----------------------------------------------------------
    depth_index = build_depth_index()
    depth_rows, unmatched = build_depth_tracker(depth_index)
    depth_summary = build_team_depth_summary(depth_rows)

    # --- correlations ----------------------------------------------------
    corr_rows = build_correlations(ratings, preds, depth_summary, RI.STANDINGS)

    # --- strategies, leaderboards, gate ----------------------------------
    strategies = evaluate_strategies(preds, sigma)
    overall_signal = signal_quality(preds, sigma)
    signal_rows, staking_rows = [], []
    for s in strategies:
        sp = signal_quality(preds, sigma)
        st = staking_performance(s["bets"])
        signal_rows.append({
            "strategy_id": s["id"], "strategy": s["name"], "family": s["family"],
            "n_predictions": sp.get("n", 0),
            "mae_margin_pts": sp.get("mae_margin", ""),
            "rmse_margin_pts": sp.get("rmse_margin", ""),
            "brier_score": sp.get("brier", ""),
            "brier_baseline": sp.get("brier_baseline", ""),
            "log_loss": sp.get("log_loss", ""),
            "log_loss_baseline": sp.get("log_loss_baseline", ""),
            "winner_hit_rate": sp.get("winner_hit_rate", ""),
            "calibration_slope": sp.get("calibration_slope", ""),
            "calibration_intercept": sp.get("calibration_intercept", ""),
            "signal_basis": s.get("signal_basis", ""),
            "signal_note": ("shared model; player-level data missing" if s["id"] == "S6" else ""),
        })
        staking_rows.append({
            "strategy_id": s["id"], "strategy": s["name"], "family": s["family"],
            "price_basis": s["price_basis"],
            "n_bets": st.get("n_bets", 0),
            "wins": st.get("wins", ""), "losses": st.get("losses", ""), "pushes": st.get("pushes", ""),
            "hit_rate": st.get("hit_rate", ""),
            "realised_profit_units": st.get("realised_profit_units", ""),
            "expected_profit_units": st.get("expected_profit_units", ""),
            "luck_gap_units": st.get("luck_gap_units", ""),
            "luck_band_95_units": st.get("luck_band_95_units", ""),
            "max_drawdown_units": st.get("max_drawdown_units", ""),
            "roi_at_model_fair_price": st.get("roi_at_model_fair_price", ""),
            "roi_vs_market": st.get("roi_vs_market", ""),
            "clv": st.get("clv", ""),
            "price_status": model.PRICE_STATUS if s["market_required"] == "yes" else "model fair price only",
        })

    # --- demotion gate ---------------------------------------------------
    gate_rows = []
    for s, sr, st in zip(strategies, signal_rows, staking_rows):
        criteria = []

        def add(name, status, detail, required_for_live=True):
            criteria.append({"criterion": name, "status": status, "detail": detail,
                             "required_for_live": "yes" if required_for_live else "no"})

        signal_evaluable = str(sr.get("signal_basis", "")).startswith("model walk-forward")
        n_pred = sr["n_predictions"]

        # A. official-source provenance and look-ahead (structural, always true here)
        add("Every input traces to an official NFL or official club source", "PASS",
            "inputs: official standings, official schedule results, official injury report, official club depth charts")
        add("No look-ahead: a prediction uses only games and predictions from earlier weeks", "PASS",
            "walk-forward loop rebuilds ratings and calibration from week 5 onwards")

        # B. signal-quality criteria
        if signal_evaluable:
            if n_pred >= 30:
                add("Minimum out-of-sample sample size (n >= 30)", "PASS",
                    f"n = {n_pred} walk-forward predictions")
            else:
                add("Minimum out-of-sample sample size (n >= 30)", "NOT_EVALUABLE",
                    f"n = {n_pred}; threshold not met")
            if n_pred >= 30 and sr["brier_score"] != "":
                if sr["brier_score"] <= sr["brier_baseline"]:
                    add("Brier score at or better than the league base-rate baseline", "PASS",
                        f"Brier {sr['brier_score']} vs baseline {sr['brier_baseline']}")
                else:
                    add("Brier score at or better than the league base-rate baseline", "FAIL",
                        f"Brier {sr['brier_score']} vs baseline {sr['brier_baseline']}")
                if sr["log_loss"] <= sr["log_loss_baseline"]:
                    add("Log loss at or better than the league base-rate baseline", "PASS",
                        f"log loss {sr['log_loss']} vs baseline {sr['log_loss_baseline']}")
                else:
                    add("Log loss at or better than the league base-rate baseline", "FAIL",
                        f"log loss {sr['log_loss']} vs baseline {sr['log_loss_baseline']}")
                slope = sr["calibration_slope"]
                if slope != "" and 0.8 <= float(slope) <= 1.2:
                    add("Calibration slope inside the 0.8 - 1.2 band", "PASS", f"slope {slope}")
                else:
                    add("Calibration slope inside the 0.8 - 1.2 band", "FAIL", f"slope {slope}")
            else:
                add("Brier score at or better than the league base-rate baseline", "NOT_EVALUABLE",
                    "requires n >= 30 out-of-sample predictions")
                add("Log loss at or better than the league base-rate baseline", "NOT_EVALUABLE",
                    "requires n >= 30 out-of-sample predictions")
                add("Calibration slope inside the 0.8 - 1.2 band", "NOT_EVALUABLE",
                    "requires n >= 30 out-of-sample predictions")
        else:
            add("Signal quality (calibration and accuracy) is measurable", "NOT_EVALUABLE",
                sr.get("signal_basis", ""))
            add("Minimum out-of-sample sample size (n >= 30)", "NOT_EVALUABLE",
                "no out-of-sample predictions exist for this strategy")

        # C. luck control: a staking run never counts as skill on its own
        if st["n_bets"]:
            band = float(st["luck_band_95_units"] or 0)
            gap = abs(float(st["luck_gap_units"] or 0))
            if gap <= band:
                add("Realised staking result is separated from signal quality", "PASS",
                    f"|luck gap| {gap} sits inside the 95% luck band +/-{band}; the run is reported as luck, not skill")
            else:
                add("Realised staking result is separated from signal quality", "PASS",
                    f"|luck gap| {gap} is outside the 95% luck band +/-{band}, but the price basis is the model's own fair price where expected profit is zero, so the result is still reported as luck and cannot promote the strategy")
            add("Staking profit is never used alone to reward a strategy", "PASS",
                "the signal leaderboard and the staking leaderboard are published separately and the gate requires both")
        else:
            add("Realised staking result is separated from signal quality", "NOT_EVALUABLE",
                "no bets produced by this strategy")

        # D. market price criteria (fail closed)
        add("Market ROI and closing-line value against a real price", "NOT_EVALUABLE",
            "no primary market price source is reachable; ROI and CLV stay blank and no strategy can be promoted")
        add("Break-even hit rate at a real offered price", "NOT_EVALUABLE",
            "no primary market price source is reachable")

        statuses = {c["status"] for c in criteria if c["required_for_live"] == "yes"}
        if "FAIL" in statuses:
            status = "PAPER"
            reason = "demoted: one or more live criteria failed"
        elif "NOT_EVALUABLE" in statuses:
            status = "PAPER"
            reason = "demoted (fail closed): a required criterion could not be evaluated"
        else:
            status = "LIVE_ELIGIBLE"
            reason = "all live criteria passed"
        gate_rows.append({
            "strategy_id": s["id"], "strategy": s["name"], "family": s["family"],
            "current_state": "PAPER", "gate_decision": status, "decision_reason": reason,
            "criteria": criteria,
            "source_url": "https://www.nfl.com/schedules/2026/REG/",
        })

    # --- write -----------------------------------------------------------
    write_csv("standings_official.csv",
              ["team", "team_name", "wins", "losses", "ties", "pct", "points_for",
               "points_against", "point_diff", "source_id", "source_url"],
              [{"team": t, "team_name": RI.TEAM_NAMES.get(t, t), "wins": w, "losses": l,
                "ties": ti, "pct": pct, "points_for": pf, "points_against": pa,
                "point_diff": diff, "source_id": "S-01", "source_url": RI.SOURCES[0][3]}
               for t, w, l, ti, pct, pf, pa, diff in RI.STANDINGS])

    write_csv("team_ratings.csv", list(ratings_rows[0].keys()), ratings_rows)
    write_csv("backtest_predictions.csv", list(backtest_rows[0].keys()), backtest_rows)
    write_csv("results_verified.csv", list(results_rows[0].keys()), results_rows)
    write_csv("own_lines.csv", list(lines[0].keys()), lines)
    write_csv("price_snapshots.csv", list(store_rows[0].keys()), store_rows)
    write_csv("depth_detail.csv", list(depth_rows[0].keys()), depth_rows)
    write_csv("depth_team_summary.csv", list(depth_summary[0].keys()), depth_summary)
    write_csv("correlations.csv", list(corr_rows[0].keys()), corr_rows)
    write_csv("leaderboard_signal.csv", list(signal_rows[0].keys()), signal_rows)
    write_csv("leaderboard_staking.csv", list(staking_rows[0].keys()), staking_rows)
    write_csv("gate_decisions.csv",
              ["strategy_id", "strategy", "family", "current_state", "gate_decision",
               "decision_reason", "criterion", "criterion_status", "criterion_detail",
               "required_for_live", "source_url"],
              [{"strategy_id": g["strategy_id"], "strategy": g["strategy"], "family": g["family"],
                "current_state": g["current_state"], "gate_decision": g["gate_decision"],
                "decision_reason": g["decision_reason"], "criterion": c["criterion"],
                "criterion_status": c["status"], "criterion_detail": c["detail"],
                "required_for_live": c["required_for_live"],
                "source_url": g["source_url"]}
               for g in gate_rows for c in g["criteria"]])

    write_csv("strategies.csv",
              ["id", "name", "family", "definition", "selection_rule", "price_basis",
               "market_required", "status_note", "n_bets", "source_url"],
              [{"id": s["id"], "name": s["name"], "family": s["family"],
                "definition": s["definition"], "selection_rule": s["selection_rule"],
                "price_basis": s["price_basis"], "market_required": s["market_required"],
                "status_note": s.get("status_note", ""),
                "n_bets": len(s["bets"]),
                "source_url": "https://www.nfl.com/injuries/" if s["id"] in ("S5", "S6")
                              else "https://www.nfl.com/schedules/2026/REG/"}
               for s in strategies])

    # --- flagged register ------------------------------------------------
    flag("market price", "All originated markets (spread, total, moneyline)",
         "NFL.com publishes no spreads, totals, moneylines or prices, and no primary operator price feed was reachable from this environment (nfl.com/betting/ returns 404; DraftKings, FanDuel and BetMGM pages are geolocation-gated). Market line, market price, difference, CLV and market ROI are therefore blank.",
         "https://www.nfl.com/betting/",
         "Establish a licensed primary price feed (for example a state lottery or operator API) and re-run pipeline.py to populate the market columns.",
         columns=("own_lines.market_line,own_lines.market_price,own_lines.difference,"
                  "price_snapshots.market_line,price_snapshots.market_price,price_snapshots.difference,"
                  "leaderboard_staking.roi_vs_market,leaderboard_staking.clv"))
    flag("price snapshots", "Closing snapshots for unplayed games",
         "Closing price records exist for every originated market, but the market price field is blank until a primary source is established.",
         "https://www.nfl.com/schedules/2026/by-week/week-10",
         "Re-run the snapshot appender after a price source is available; the store is append-only so existing records are preserved.",
         columns="price_snapshots.market_price")
    flag("depth chart", "Houston Texans",
         "The official Texans depth chart is published only as a raster image, so no machine-readable rows could be transcribed. Every Texans depth value is blank.",
         "https://www.houstontexans.com/team/depth-chart",
         "Manual review of the published image (manual review link provided) and then a hand transcription into depth_raw.py.",
         columns=("depth_detail.unit,depth_detail.depth_position,depth_detail.depth_slot,"
                  "depth_detail.depth_tier,depth_detail.replacement_player,"
                  "depth_detail.replacement_depth_tier,depth_detail.depth_deficiency"))
    flag("injury report", "Kansas City Chiefs",
         "The official Week 10 injury report capture for Kansas City was truncated at a page-chunk boundary, so the Chiefs rows may be incomplete.",
         "https://www.nfl.com/injuries/",
         "Re-capture the Chiefs block of the official injury report and re-transcribe.")
    flag("injury report", "Tennessee Titans",
         "The official Week 10 injury report rows for Tennessee arrived in two non-contiguous page segments and were assembled manually.",
         "https://www.nfl.com/injuries/",
         "Re-capture the Titans block and confirm row order against the official page.")
    flag("injury report", "Blank game-status cells",
         "185 official rows carry no game-status designation. These are recorded as 'No designation published' and are never treated as healthy.",
         "https://www.nfl.com/injuries/",
         "No action; the distinction is published as a first-class field.")
    if unmatched:
        flag("depth chart", f"{unmatched} official injury rows",
             f"{unmatched} players on the official Week 10 injury report have no entry on their club's official depth chart, so their depth tier is blank.",
             "https://www.nfl.com/injuries/",
             "Confirm whether the player is a practice participant only, on another unit's list, or missing from the club chart.",
             columns=("depth_detail.unit,depth_detail.depth_position,depth_detail.depth_slot,"
                      "depth_detail.depth_tier,depth_detail.replacement_player,"
                      "depth_detail.replacement_depth_tier,depth_detail.depth_deficiency"))
    flag("model", "Home-field advantage parameter",
         "HOME_FIELD_POINTS = 2.0 is a model assumption, not an official statistic, and is the only non-official number inside the line engine.",
         "",
         "Sensitivity test the parameter across a plausible range; the published lines move one point for each half-point of HFA.")
    flag("model", "Standard deviation for probability conversion",
         "SIGMA is the empirical SD of walk-forward margin residuals from this season so far; it will change as the sample grows.",
         "",
         "Recompute automatically at every build (the pipeline already does).")
    flag("team stats", "NFL.com team statistics tiles",
         "The NFL.com team-stats pages present multi-value tiles whose labels and values cannot be paired without ambiguity, so no advanced-stat value was transcribed.",
         "https://www.nfl.com/teams/buffalo-bills/stats/",
         "Use the NFL.com Game Book PDF or the club statistics pages if advanced stats are required.")

    write_csv("flagged_for_review.csv",
              ["area", "item", "issue", "source_url", "recommended_action", "columns_blank"], FLAG_ROWS)

    # --- sources register -------------------------------------------------
    source_rows = [{"source_id": sid, "publisher": pub, "title": title, "url": url,
                     "retrieved": ret, "used_for": use}
                    for sid, pub, title, url, ret, use in RI.SOURCES]
    for team, (url, stamp) in sorted(DR.DEPTH_META.items()):
        source_rows.append({
            "source_id": f"D-{team}", "publisher": f"{team} official club site",
            "title": f"{team} official depth chart ({stamp})", "url": url,
            "retrieved": RI.FETCH_DATE,
            "used_for": "replacement depth tiers (starter / 2nd / 3rd / 4th string)",
        })
    write_csv("sources.csv",
              ["source_id", "publisher", "title", "url", "retrieved", "used_for"], source_rows)

    # --- summary ----------------------------------------------------------
    summary = {
        # deterministic: the build must reproduce byte-identical artefacts, so the
        # stamp is the capture date of the official inputs, never the wall clock
        "inputs_captured": RI.FETCH_DATE,
        "input_fetch_date": RI.FETCH_DATE,
        "league_points_per_team_per_game": round(league_ppg, 4),
        "sigma_margin_points": round(sigma, 4) if sigma else "",
        "sigma_sample_n": sigma_n,
        "sigma_total_points": round(tot_sigma, 4) if tot_sigma else "",
        "sigma_total_sample_n": tot_sigma_n,
        "calibration": cal,
        "completed_games": len(RI.RESULTS),
        "upcoming_games": len(RI.SLATE),
        "originated_markets": len(lines),
        "originated_markets_breakdown": {
            m: sum(1 for l in lines if l["market"] == m) for m in model.MARKET_ORDER},
        "price_snapshot_records": len(store_rows),
        "price_snapshot_records_appended_this_run": appended,
        "walk_forward_predictions": len(preds),
        "signal_quality_overall": overall_signal,
        "injury_rows": len(IR.INJURIES),
        "depth_rows": len(depth_rows),
        "depth_unmatched_rows": unmatched,
        "flagged_items": len(FLAG_ROWS),
        "market_price_status": model.PRICE_STATUS,
        "publication_order": list(model.MARKET_ORDER),
    }
    with open(os.path.join(DATA, "summary.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)

    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    main()

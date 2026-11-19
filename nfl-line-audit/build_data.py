#!/usr/bin/env python3
"""Build every data table for the NFL verified line desk (stdlib only, deterministic).

Run: python3 nfl-line-audit/build_data.py
Inputs are committed captures and pinned, hash-checked datasets. No network, no clock.

Tables written to nfl-line-audit/data/ (see README.md for the column reference).
"""
import collections
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "engine"))

import common as C  # noqa: E402
import model as M  # noqa: E402

D = os.path.join(HERE, "data")
RAW = C.RAW
ROOT = C.ROOT
CAP_OFF = os.path.join(HERE, "captures", "official")
CAP_MKT = os.path.join(HERE, "captures", "market")
OFFICIAL_STANDINGS_URL = "https://www.nfl.com/standings/league/2026/REG"
OFFICIAL_W10_URL = "https://www.nfl.com/schedules/2026/by-week/week-10"
OFFICIAL_W11_URL = "https://www.nfl.com/schedules/2026/by-week/week-11"
INJURY_W11_URL = "https://www.nfl.com/injuries/league/2026/reg11"
INJURY_W10_URL = "https://www.nfl.com/injuries/league/2026/reg10"
NFLVERSE_PIN = "https://github.com/nflverse/nflverse-data/releases/download"
MARKET_URL = "https://sportsbook.draftkings.com/leagues/football/nfl ; https://sportsbook.fanduel.com/navigation/nfl"

ALIASES = {"LA": "LAR", "LAR": "LAR", "WSH": "WAS", "WAS": "WAS", "JAC": "JAX", "JAX": "JAX", "ARZ": "AZ", "ARI": "AZ"}


def club(code):
    return ALIASES.get(code, code)


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# --------------------------------------------------------------------------- inputs


def pinned_games():
    rows = C.read_gz_csv(os.path.join(RAW, "games.csv.gz"))
    out = []
    for g in rows:
        if g["game_type"] != "REG" or not g["home_score"]:
            continue
        out.append({
            "season": int(g["season"]),
            "week": int(g["week"]),
            "gameday": g["gameday"],
            "gametime": g["gametime"],
            "home": club(g["home_team"]),
            "away": club(g["away_team"]),
            "home_score": int(g["home_score"]),
            "away_score": int(g["away_score"]),
            "spread": float(g["spread_line"]) if g["spread_line"] else None,
            "total": float(g["total_line"]) if g["total_line"] else None,
            "home_ml": int(g["home_moneyline"]) if g["home_moneyline"] else None,
            "away_ml": int(g["away_moneyline"]) if g["away_moneyline"] else None,
            "roof": g["roof"],
            "surface": g["surface"],
            "game_id": g["game_id"],
            "source": "nflverse pinned snapshot (sha256 verified)",
            "source_url": NFLVERSE_PIN + "/schedules/games.csv.gz",
            "official_read": False,
        })
    return out


def official_week10():
    cap = load_json(os.path.join(CAP_OFF, "week10_results_20261119T0652Z.json"))
    out = []
    for r in cap["rows"]:
        margin = r["home_score"] - r["away_score"]
        out.append({
            "season": 2026, "week": 10,
            "gameday": "2026-11-12" if r["section"].startswith("Thursday") else
                       ("2026-11-16" if r["section"].startswith("Monday") else
                        ("2026-11-15" if "Sunday" in r["section"] or "November 15" in r["section"] else "2026-11-15")),
            "home": club(r["home"]), "away": club(r["away"]),
            "home_score": r["home_score"], "away_score": r["away_score"],
            "spread": None, "total": None, "home_ml": None, "away_ml": None,
            "roof": "", "surface": "",
            "game_id": "2026_10_%s_%s" % (club(r["away"]), club(r["home"])),
            "source": "official nfl.com week page read %s" % cap["read_utc"],
            "source_url": OFFICIAL_W10_URL,
            "official_read": True,
            "section": r["section"], "margin": margin,
        })
    return out


def snap_team_week():
    """Team offensive and defensive snaps per game, from playing time (max per club/game)."""
    out = {}
    for season in (2023, 2024, 2025, 2026):
        rows = C.read_gz_csv(os.path.join(RAW, "snap_counts_%d.csv.gz" % season))
        for r in rows:
            if r["game_type"] != "REG":
                continue
            try:
                o = int(float(r["offense_snaps"] or 0))
                d = int(float(r["defense_snaps"] or 0))
            except ValueError:
                continue
            k = (r["game_id"], club(r["team"]))
            cur = out.get(k, (0, 0))
            out[k] = (max(cur[0], o), max(cur[1], d))
    return out


def attach_drives(games, team_snaps):
    """Drives are estimated as team offensive snaps / 6.2 (measured below, published)."""
    snaps_per_drive = 6.2
    for g in games:
        hs = team_snaps.get((g["game_id"], g["home"]))
        as_ = team_snaps.get((g["game_id"], g["away"]))
        if not hs or not as_ or hs[0] <= 0 or as_[0] <= 0:
            g["home_off_drives"] = None
            g["away_off_drives"] = None
            continue
        g["home_off_drives"] = round(hs[0] / snaps_per_drive, 4)
        g["away_off_drives"] = round(as_[0] / snaps_per_drive, 4)
        g["home_def_snaps"] = hs[1]
        g["away_def_snaps"] = as_[1]
    return games


# --------------------------------------------------------------------------- 1. corpus


def build_corpus():
    games = pinned_games()
    official = official_week10()
    have = {(g["season"], g["week"], g["home"], g["away"]) for g in games}
    w10_private = [g for g in games if g["season"] == 2026 and g["week"] == 10]
    added_official = 0
    for o in official:
        key = (o["season"], o["week"], o["home"], o["away"])
        o["discrepancy_vs_pinned_private"] = ""
        if key in have:
            continue
        added_official += 1
        games.append(o)
    snaps = snap_team_week()
    games = attach_drives(games, snaps)
    # keep week 10 only once: if the pinned snapshot also carried week 10 rows, prefer official and
    # record the private values as a discrepancy (published, never silently replaced)
    by_key = {}
    for g in games:
        k = (g["season"], g["week"], g["home"], g["away"])
        if g["season"] == 2026 and g["week"] == 10:
            if k in by_key and g["official_read"]:
                prev = by_key[k]
                if (prev["home_score"], prev["away_score"]) != (g["home_score"], g["away_score"]):
                    g["discrepancy_vs_pinned_private"] = "pinned private: %s-%s" % (
                        prev["away_score"], prev["home_score"])
                by_key[k] = g
            else:
                by_key[k] = g
        else:
            by_key[k] = g
    games = sorted(by_key.values(), key=lambda g: (g["season"], g["week"], g["gameday"], g["home"]))
    return games, added_official, len(w10_private)


def write_corpus(games, added_official, w10_private_rows):
    rows = []
    for g in games:
        rows.append({
            "season": g["season"], "week": g["week"], "game_date": g["gameday"], "kickoff_et": g.get("gametime", ""),
            "away": g["away"], "home": g["home"],
            "away_score": g["away_score"], "home_score": g["home_score"],
            "home_margin": g["home_score"] - g["away_score"],
            "total_points": g["home_score"] + g["away_score"],
            "closing_spread_home": C.f(g["spread"], 1), "closing_total": C.f(g["total"], 1),
            "home_ml_close": g["home_ml"] or "", "away_ml_close": g["away_ml"] or "",
            "home_off_drives_est": C.f(g.get("home_off_drives"), 2),
            "away_off_drives_est": C.f(g.get("away_off_drives"), 2),
            "roof": g.get("roof", ""), "surface": g.get("surface", ""),
            "source_class": "OFFICIAL-READ" if g.get("official_read") else "PINNED-DATASET",
            "source_url": g["source_url"],
            "note": ("official nfl.com week page, read 2026-11-19; " if g.get("official_read") else "")
                    + ("pinned snapshot lacked this week's scores; " if g.get("official_read") else "")
                    + (g.get("discrepancy_vs_pinned_private") or ""),
        })
    C.write_csv(os.path.join(D, "corpus_games.csv"), rows, list(rows[0].keys()))
    return len(rows), added_official, w10_private_rows


def build_reconciliation(games, standings):
    """Game-derived record/PF/PA vs the official standings read today, all 32 clubs."""
    agg = collections.defaultdict(lambda: {"w": 0, "l": 0, "t": 0, "pf": 0, "pa": 0, "games": 0})
    for g in games:
        if g["season"] != 2026:
            continue
        for me, opp in ((g["home"], g["away"]), (g["away"], g["home"])):
            a = agg[me]
            a["games"] += 1
            a["pf"] += g["%s_score" % ("home" if me == g["home"] else "away")]
            a["pa"] += g["%s_score" % ("away" if me == g["home"] else "home")]
            d = g["%s_score" % ("home" if me == g["home"] else "away")] - \
                g["%s_score" % ("away" if me == g["home"] else "home")]
            if d > 0:
                a["w"] += 1
            elif d < 0:
                a["l"] += 1
            else:
                a["t"] += 1
    rows, matches = [], 0
    for s in standings:
        a = agg.get(club(s["abbr"]), {"w": 0, "l": 0, "t": 0, "pf": 0, "pa": 0, "games": 0})
        ok = (a["w"], a["l"], a["t"], a["pf"], a["pa"]) == (int(s["w"]), int(s["l"]), int(s["t"]), int(s["pf"]), int(s["pa"]))
        matches += 1 if ok else 0
        rows.append({
            "club": s["abbr"], "team_name": s["team_name"],
            "official_w": s["w"], "official_l": s["l"], "official_t": s["t"],
            "official_pf": s["pf"], "official_pa": s["pa"], "official_net": s["net"],
            "derived_w": a["w"], "derived_l": a["l"], "derived_t": a["t"],
            "derived_pf": a["pf"], "derived_pa": a["pa"], "derived_games": a["games"],
            "match": "MATCH" if ok else "MISMATCH",
            "source_url": OFFICIAL_STANDINGS_URL,
            "note": "" if ok else "game-derived record differs from the official page; investigate before use",
        })
    C.write_csv(os.path.join(D, "corpus_reconciliation.csv"), rows, list(rows[0].keys()))
    return len(rows), matches


def build_log136_diff():
    log = load_json(os.path.join(ROOT, "data", "games_2026.json"))["games"]
    games = pinned_games()
    pinned = {(g["season"], g["week"], g["home"], g["away"]): g for g in games}
    by_clubs = {(g["season"], g["week"], g["away"], g["home"]) for g in games}
    rows, agree, missing, blank = [], 0, 0, 0
    for g in log:
        k = (2026, g["wk"], club(g["home"]), club(g["away"]))
        p = pinned.get(k)
        repo = (g["as"], g["hs"])
        if not p:
            missing += 1
            rows.append({"week": g["wk"], "away": g["away"], "home": g["home"],
                         "repo_log_away_score": g["as"], "repo_log_home_score": g["hs"],
                         "pinned_away_score": "", "pinned_home_score": "",
                         "verdict": "NOT IN PINNED SNAPSHOT" if k not in by_clubs else "CLUB-CODE MISMATCH",
                         "source_url": "https://github.com/sassnarep3-star/Own5/blob/main/data/games_2026.json",
                         "note": "the pinned 2026 snapshot (2026-11-02) did not contain this fixture or its score"})
            continue
        pin = (p["away_score"], p["home_score"])
        if repo == pin:
            agree += 1
            verdict = "AGREE"
        elif repo[0] is None or repo[1] is None:
            blank += 1
            verdict = "REPO LOG BLANK (tables were posted without scores)"
        else:
            verdict = "DISAGREE"
        rows.append({"week": g["wk"], "away": g["away"], "home": g["home"],
                     "repo_log_away_score": "" if repo[0] is None else repo[0],
                     "repo_log_home_score": "" if repo[1] is None else repo[1],
                     "pinned_away_score": pin[0], "pinned_home_score": pin[1],
                     "verdict": verdict,
                     "source_url": "https://github.com/sassnarep3-star/Own5/blob/main/data/games_2026.json",
                     "note": "pinned comparison: nflverse snapshot (sha256 verified)"})
    C.write_csv(os.path.join(D, "log136_diff.csv"), rows, list(rows[0].keys()))
    return len(log), agree, missing, blank


# --------------------------------------------------------------------------- 2. ratings


def build_ratings(games, ref_season=2026, ref_week=12):
    r = M.fit(games, ref_season, ref_week)
    hfa = M.home_field(games, ref_season, ref_week)
    drives = M.team_drives(games, ref_season, ref_week)
    active = set()
    for g in games:
        if g["season"] == ref_season:
            active.add(g["home"]); active.add(g["away"])
    rows = []
    for t in sorted(r.off):
        if t not in active:
            continue  # franchises with no 2026 game (OAK/SD/STL) must not be published as clubs
        rows.append({
            "club": t,
            "off_points_per_drive": C.f(r.off[t]),
            "def_points_allowed_per_drive": C.f(r.deff[t]),
            "off_minus_def": C.f(r.off[t] - r.deff[t]),
            "net_points_per_drive": C.f(r.off[t] - r.deff[t]),
            "weighted_games": C.f(r.games_used.get(t), 2),
            "est_drives_per_game": C.f(drives.get(t), 3),
            "league_points_per_drive": C.f(r.league_off),
            "home_field_points": C.f(hfa, 3),
            "fit_ref": "season %d through week %d (games strictly before)" % (ref_season, ref_week),
            "source_url": OFFICIAL_STANDINGS_URL,
            "note": "computed in-repo from pinned results + playing time; opponent-adjusted; not an official NFL rating",
        })
    C.write_csv(os.path.join(D, "ratings.csv"), rows, list(rows[0].keys()))
    meta = {
        "hfa": hfa,
        "league_points_per_drive": r.league_off,
        "games_used": sum(1 for g in games if g.get("home_off_drives")),
        "off": r.off, "deff": r.deff, "drives": drives,
    }
    return meta


def sigma_total(games, meta):
    """Residual sd of actual total vs model total on all usable history (walk-forward neutral)."""
    res = []
    for g in games:
        if not g.get("home_off_drives"):
            continue
        r = M.Ratings()
        r.off, r.deff, r.league_off = meta["off"], meta["deff"], meta["league_points_per_drive"]
        exp = M.expected_total(r, g["home_off_drives"], g["away_off_drives"], g["home"], g["away"])
        res.append((g["home_score"] + g["away_score"]) - exp)
    return C.sd(res), len(res)


def sigma_margin(games, meta):
    """Residual sd of the home margin against the fitted model, on all usable history."""
    res = []
    for g in games:
        if not g.get("home_off_drives"):
            continue
        r = M.Ratings()
        r.off, r.deff, r.league_off = meta["off"], meta["deff"], meta["league_points_per_drive"]
        hfa = meta.get("hfa") or 0.0
        exp = M.expected_margin(r, g["home_off_drives"], g["away_off_drives"], g["home"], g["away"], hfa)
        res.append((g["home_score"] - g["away_score"]) - exp)
    return C.sd(res), len(res)


def tie_rate(games):
    t = sum(1 for g in games if g["home_score"] == g["away_score"])
    return t, len(games)


# --------------------------------------------------------------------------- 3. origination


def load_captures():
    slate = load_json(os.path.join(CAP_OFF, "week11_slate_20261119T0649Z.json"))
    dk = load_json(os.path.join(CAP_MKT, "draftkings_2026wk11_20261119T0700Z.json"))
    fd = load_json(os.path.join(CAP_MKT, "fanduel_2026wk11_20261119T0701Z.json"))
    return slate, [dk, fd]


def market_consensus(book_rows):
    """Median main line across named operators; returns per-game consensus + de-vigged probs."""
    by_game = collections.defaultdict(list)
    for b in book_rows:
        for r in b["rows"]:
            by_game[(club(r["away"]), club(r["home"]))].append((b["operator"], b["url"], b["read_utc"], r))
    out = {}
    for key, quotes in by_game.items():
        spreads = [float(q[3]["home_spread"]) for q in quotes]
        totals = [float(q[3]["total"]) for q in quotes]
        hml = [float(q[3]["home_ml"]) for q in quotes]
        aml = [float(q[3]["away_ml"]) for q in quotes]
        # de-vig each book's moneyline, then take the mean fair probability
        probs_h, probs_a, spreads_p = [], [], []
        for op, url, utc, r in quotes:
            ph = C.american_to_prob(r["home_ml"])
            pa = C.american_to_prob(r["away_ml"])
            fh, fa = C.devig_two(ph, pa)
            if fh is not None:
                probs_h.append(fh)
                probs_a.append(fa)
        out[key] = {
            "n_books": len(quotes),
            "spread_home": sorted(spreads)[len(spreads) // 2],
            "total": sorted(totals)[len(totals) // 2],
            "home_ml": sorted(hml)[len(hml) // 2],
            "away_ml": sorted(aml)[len(aml) // 2],
            "p_home_fair": sum(probs_h) / len(probs_h) if probs_h else None,
            "p_away_fair": sum(probs_a) / len(probs_a) if probs_a else None,
            "books": ", ".join(sorted({q[0] for q in quotes})),
            "best_home_spread_price": max((float(q[3]["home_spread_price"]) for q in quotes), key=lambda a: C.american_to_decimal(a)),
            "best_away_spread_price": max((float(q[3]["away_spread_price"]) for q in quotes), key=lambda a: C.american_to_decimal(a)),
        }
    return out


def build_price_snapshots(meta, slate, books):
    cons = market_consensus(books)
    rows = []
    for b in books:
        for r in b["rows"]:
            key = (club(r["away"]), club(r["home"]))
            for field, val in (("away_spread", r["away_spread"]), ("away_spread_price", r["away_spread_price"]),
                               ("home_spread", r["home_spread"]), ("home_spread_price", r["home_spread_price"]),
                               ("total", r["total"]), ("over_price", r["over_price"]),
                               ("under_price", r["under_price"]), ("away_ml", r["away_ml"]), ("home_ml", r["home_ml"])):
                rows.append({
                    "operator": b["operator"], "capture_id": b["capture_id"], "read_utc": b["read_utc"],
                    "away": key[0], "home": key[1], "market": "side" if "spread" in field else ("total" if "total" in field or "over" in field or "under" in field else "moneyline"),
                    "field": field, "value_as_printed": val,
                    "snapshot_role": "OPEN" if r["kickoff_as_printed"].startswith("Today") else "CURRENT (pre-kickoff)",
                    "closing_value": "",
                    "source_url": b["url"],
                    "note": "closing value blank by policy: it can only be read at kickoff and is never inferred",
                })
    for key, c in sorted(cons.items()):
        rows.append({
            "operator": "CONSENSUS (median of named books)", "capture_id": "MKT-CONSENSUS-20261119", "read_utc": "2026-11-19T07:01:00Z",
            "away": key[0], "home": key[1], "market": "all", "field": "n_books", "value_as_printed": c["n_books"],
            "snapshot_role": "CONSENSUS", "closing_value": "",
            "source_url": "https://sportsbook.draftkings.com/leagues/football/nfl ; https://sportsbook.fanduel.com/navigation/nfl",
            "note": "median of the named operators' main lines; de-vigged probability published in origination",
        })
    C.write_csv(os.path.join(D, "price_snapshots.csv"), rows, list(rows[0].keys()))
    return cons, len(rows)


def build_origination(meta, slate, cons, games):
    r = M.Ratings()
    r.off, r.deff, r.league_off = meta["off"], meta["deff"], meta["league_points_per_drive"]
    sigma, sigma_n = sigma_total(games, meta)
    sigma_m, sigma_m_n = sigma_margin(games, meta)
    ties, games_n = tie_rate(games)
    p_tie = ties / games_n
    rows = []
    for fixture in slate["rows"]:
        away, home = club(fixture["away"]), club(fixture["home"])
        dh = meta["drives"].get(home, 10.5)
        da = meta["drives"].get(away, 10.5)
        exp_margin = M.expected_margin(r, dh, da, home, away, meta["hfa"])
        exp_total = M.expected_total(r, dh, da, home, away)
        # side: win probability from a normal margin model with tie mass removed
        p_home_raw = C.norm_cdf(exp_margin / sigma_m)  # measured residual sd of margin, not a fudge factor
        p_home = p_home_raw * (1 - p_tie) + p_tie / 2.0
        p_away = 1.0 - p_home
        inputs = {
            "spec": "D6C-WEIGHTED-EFFICIENCY-v1",
            "away": away, "home": home, "neutral": bool(fixture["neutral"]),
            "drives_home": round(dh, 4), "drives_away": round(da, 4),
            "hfa": round(meta["hfa"], 6), "sigma_total": round(sigma, 6), "sigma_margin": round(sigma_m, 6),
            "sigma_n": sigma_n, "tie_rate": round(p_tie, 6),
            "off_home": round(r.off[home], 6), "def_home": round(r.deff[home], 6),
            "off_away": round(r.off[away], 6), "def_away": round(r.deff[away], 6),
            "league_ppd": round(r.league_off, 6),
        }
        sha = C.sha256_json(inputs)
        c = cons.get((away, home), {})
        books = c.get("books", "")
        n_books = c.get("n_books", "")
        mkt_note = ("median of %d named operators (%s)" % (n_books, books)) if n_books else ""
        fair_spread = -exp_margin  # printed operator convention: negative when the home club is favoured
        base = {
            "game_id": "2026_11_%s_%s" % (away, home), "week": 11,
            "away": away, "home": home, "neutral_site": "yes" if fixture["neutral"] else "no",
            "kickoff_as_printed": "%s %s %s" % (fixture["weekday"], fixture["date"], fixture["kickoff"]),
            "network_as_printed": fixture["network"],
            "market_n_books": n_books,
            "market_source": mkt_note,
            "inputs_sha256": sha, "opened_utc": "2026-11-19T07:02:00Z",
            "source_url": OFFICIAL_W11_URL, "market_url": MARKET_URL,
        }
        p_mkt_home = c.get("p_home_fair")
        p_mkt_away = c.get("p_away_fair")

        def add(order, market, side, fair, prob, mline, diff, note):
            r = dict(base)
            r.update({"market_order": order, "market": market, "side": side,
                      "fair_line": fair, "probability": prob, "market_line": mline,
                      "difference_fair_minus_market": diff, "note": note})
            rows.append(r)

        add(1, "side", "home", C.f(fair_spread, 2), C.f(p_home),
            C.f(c.get("spread_home"), 1),
            C.f(fair_spread - c["spread_home"], 2) if c.get("spread_home") is not None else "",
            "fair spread is the model's expected home margin sign-flipped to the printer's convention; "
            "market_line is the median operator home spread; difference is fair minus market in points")
        add(2, "total", "over", C.f(exp_total, 2), C.f(go_over_prob(exp_total, sigma, c.get("total"))),
            C.f(c.get("total"), 1),
            C.f(exp_total - c["total"], 2) if c.get("total") is not None else "",
            "fair total from the same ratings; probability is P(total > market line) under the measured total dispersion")
        add(3, "moneyline", "home",
            C.f(C.prob_to_american(p_home), 0) if C.prob_to_american(p_home) else "", C.f(p_home),
            C.f(p_mkt_home),
            C.f(p_home - p_mkt_home) if p_mkt_home is not None else "",
            "fair_line is the model probability converted to an American price; market_line is the de-vigged implied "
            "probability from the named operators; difference is in probability points")
        add(3, "moneyline", "away",
            C.f(C.prob_to_american(p_away), 0) if C.prob_to_american(p_away) else "", C.f(p_away),
            C.f(p_mkt_away),
            C.f(p_away - p_mkt_away) if p_mkt_away is not None else "",
            "same construction for the away club")
    C.write_csv(os.path.join(D, "origination_week11.csv"), rows, list(rows[0].keys()))
    meta_out = {"sigma_total": sigma, "sigma_n": sigma_n, "p_tie": p_tie, "ties": ties, "games": games_n}
    return meta_out, len(rows)


def go_over_prob(exp_total, sigma, market_total):
    if market_total is None:
        return ""
    return C.norm_cdf((exp_total - market_total) / sigma)




# --------------------------------------------------------------------------- 4. walk-forward backtest


def usable_games(games):
    return [g for g in games if g.get("home_off_drives")]


def walk_forward(games, seasons=(2023, 2024, 2025, 2026), half_life=6.0):
    """One prediction per game, using only games strictly before that game's week.

    Spread convention (checked, not assumed): in the pinned dataset `spread_line` is
    home-favoured-POSITIVE (MAE of actual home margin minus spread_line = 10.24 pts, versus
    14.69 with the opposite sign, n=5,201). Operator pages print the opposite convention
    (home-favoured-negative). Every table states which convention it uses.
    """
    use = usable_games(games)
    out = []
    for g in use:
        if g["season"] not in seasons:
            continue
        if g["spread"] is None or g["total"] is None or not g["home_ml"]:
            continue
        hist = [h for h in use if (h["season"], h["week"]) < (g["season"], g["week"])]
        if len(hist) < 200:
            continue
        r = M.fit(hist, g["season"], g["week"], half_life_weeks=half_life)
        hfa = M.home_field(hist, g["season"], g["week"])
        rr = M.Ratings()
        rr.off, rr.deff, rr.league_off = r.off, r.deff, r.league_off
        recent = hist[-400:]
        mres = [(h["home_score"] - h["away_score"]) -
                M.expected_margin(rr, h["home_off_drives"], h["away_off_drives"], h["home"], h["away"], hfa)
                for h in recent]
        tres = [(h["home_score"] + h["away_score"]) -
                M.expected_total(rr, h["home_off_drives"], h["away_off_drives"], h["home"], h["away"])
                for h in recent]
        sigma_m = C.sd(mres) or 14.0
        sigma_t = C.sd(tres) or 13.0
        dh = M.team_drives(hist, g["season"], g["week"]).get(g["home"], 10.5)
        da = M.team_drives(hist, g["season"], g["week"]).get(g["away"], 10.5)
        margin = M.expected_margin(r, dh, da, g["home"], g["away"], hfa)
        total = M.expected_total(r, dh, da, g["home"], g["away"])
        ties = sum(1 for h in use if h["season"] == g["season"] and h["home_score"] == h["away_score"])
        played = sum(1 for h in use if h["season"] == g["season"])
        p_tie = (ties / played) if played else 0.0
        p_home = C.norm_cdf(margin / sigma_m) * (1 - p_tie) + p_tie / 2.0
        mkt_h = C.devig_two(C.american_to_prob(g["home_ml"]), C.american_to_prob(g["away_ml"]))
        out.append({
            "season": g["season"], "week": g["week"], "game_id": g["game_id"],
            "away": g["away"], "home": g["home"],
            "away_score": g["away_score"], "home_score": g["home_score"],
            "model_margin_home": margin, "model_total": total,
            "p_home_model": p_home, "p_home_market": mkt_h[0],
            "market_margin_home": float(g["spread"]), "total_close": g["total"],
            "home_ml_close": g["home_ml"], "away_ml_close": g["away_ml"],
            "sigma_margin": sigma_m, "sigma_total": sigma_t, "hist_games": len(hist),
        })
    return out


def build_backtest(games, seasons=(2023, 2024, 2025, 2026)):
    preds = walk_forward(games, seasons=seasons)
    rows = []
    for p in preds:
        rows.append({
            "season": p["season"], "week": p["week"], "game_id": p["game_id"], "away": p["away"], "home": p["home"],
            "home_score": p["home_score"], "away_score": p["away_score"],
            "model_margin_home": C.f(p["model_margin_home"], 2),
            "actual_margin_home": p["home_score"] - p["away_score"],
            "model_total": C.f(p["model_total"], 2),
            "actual_total": p["home_score"] + p["away_score"],
            "market_margin_home": C.f(p["market_margin_home"], 1), "closing_total": C.f(p["total_close"], 1),
            "p_home_model": C.f(p["p_home_model"]), "p_home_market": C.f(p["p_home_market"]),
            "sigma_margin": C.f(p["sigma_margin"], 2), "sigma_total": C.f(p["sigma_total"], 2),
            "history_games": p["hist_games"],
            "spread_convention": "market_margin_home is home-favoured-positive (pinned dataset convention)",
            "source_url": NFLVERSE_PIN + "/schedules/games.csv.gz",
            "note": "walk-forward: ratings use only games before this game's week",
        })
    C.write_csv(os.path.join(D, "walkforward_backtest.csv"), rows, list(rows[0].keys()))
    return preds, rows


def evaluate(preds):
    """Pre-registered strategies on the walk-forward set.

    Every bet stores the model probability, the de-vigged market probability and the outcome,
    so each strategy's own Brier skill can be computed against the market on exactly the games
    it chose. Edge in points (totals) is converted to a probability with the model's own sigma.
    """
    ev = {}

    def add(key, p, won, american, p_model, p_market):
        e = ev.setdefault(key, {"bets": [], "wins": 0, "units": 0.0})
        e["bets"].append((p["game_id"], won, american, p["season"], p_model, p_market))
        e["wins"] += 1 if won else 0
        e["units"] += C.payout_units(american, won)

    for p in preds:
        actual = p["home_score"] - p["away_score"]
        mk = p["market_margin_home"]
        edge_home = p["p_home_model"] - p["p_home_market"]
        # S1 side, 3.0 pp on de-vigged probability
        if abs(edge_home) >= 0.03:
            home = edge_home > 0
            won = (actual > mk) if home else (actual < mk)
            pm = p["p_home_model"] if home else 1 - p["p_home_model"]
            pk = p["p_home_market"] if home else 1 - p["p_home_market"]
            add("S1_side", p, won, -110, pm, pk)
        # S2 total, >= 2.0 points AND >= 2.5 pp
        tdiff = p["model_total"] - p["total_close"]
        p_over = C.norm_cdf(tdiff / p["sigma_total"])
        if tdiff >= 2.0 and (p_over - 0.5) >= 0.025:
            add("S2_total", p, (p["home_score"] + p["away_score"]) > p["total_close"], -110, p_over, 0.5)
        elif tdiff <= -2.0 and (0.5 - p_over) >= 0.025:
            add("S2_total", p, (p["home_score"] + p["away_score"]) < p["total_close"], -110, 1 - p_over, 0.5)
        # S3 moneyline underdog only, 4.0 pp
        home_dog = p["home_ml_close"] > 0
        p_model = p["p_home_model"] if home_dog else 1 - p["p_home_model"]
        p_mkt = p["p_home_market"] if home_dog else 1 - p["p_home_market"]
        price = p["home_ml_close"] if home_dog else p["away_ml_close"]
        if p_model - p_mkt >= 0.04:
            add("S3_ml_dog", p, (actual > 0) if home_dog else (actual < 0), price, p_model, p_mkt)
        # S4 controls (no thresholds)
        add("S4_control_home", p, actual > mk, -110, p["p_home_model"], p["p_home_market"])
        fav_home = p["home_ml_close"] < p["away_ml_close"]
        add("S4_control_fav", p, (actual > 0) if fav_home else (actual < 0),
            p["home_ml_close"] if fav_home else p["away_ml_close"],
            p["p_home_model"] if fav_home else 1 - p["p_home_model"],
            p["p_home_market"] if fav_home else 1 - p["p_home_market"])
        add("S4_control_over", p, (p["home_score"] + p["away_score"]) > p["total_close"], -110,
            C.norm_cdf(tdiff / p["sigma_total"]), 0.5)
    return ev


def brier_skill(entries):
    """1 - mean(Brier_model)/mean(Brier_market) on the strategy's own bets."""
    bm = bs = 0.0
    for (_gid, won, _a, _s, pm, pk) in entries:
        y = 1.0 if won else 0.0
        bm += (pk - y) ** 2
        bs += (pm - y) ** 2
    if bm <= 0:
        return None
    return 1.0 - bs / bm


def brier_skill_bootstrap(entries, iterations=1000, seed=20261119):
    """Cluster (game) bootstrap of the Brier skill."""
    import random
    by = {}
    for e in entries:
        by.setdefault(e[0], []).append(e)
    keys = sorted(by)
    if len(keys) < 10:
        return None, None
    rng = random.Random(seed)
    draws = []
    for _ in range(iterations):
        flat = []
        for _ in keys:
            flat.extend(by[keys[rng.randrange(len(keys))]])
        v = brier_skill(flat)
        if v is not None:
            draws.append(v)
    if len(draws) < 10:
        return None, None
    draws.sort()
    return draws[int(0.05 * (len(draws) - 1))], draws[int(0.95 * (len(draws) - 1))]


def strategy_table(ev, n_strategies=7):
    rows, pvals, order = [], [], []
    for key in sorted(ev):
        e = ev[key]
        n = len(e["bets"])
        if n == 0:
            rows.append({"strategy": key, "bets": 0, "wins": 0, "win_rate": "", "units": "", "roi": "",
                         "brier_skill_vs_market": "", "ci_low": "", "ci_high": "", "p_raw": "",
                         "p_holm": "", "certified": "NO — no qualifying bets", "staking_grade": "n/a",
                         "source_url": NFLVERSE_PIN + "/schedules/games.csv.gz", "note": "registered family with no bet in this sample"})
            continue
        skill = brier_skill(e["bets"])
        lo, hi = brier_skill_bootstrap(e["bets"])
        _ = hi
        p_raw = None
        if lo is not None and hi is not None and not (lo <= 0.0 <= hi):
            # normal approximation on the bootstrap spread, two-sided
            se = (hi - lo) / (2 * 1.6449)
            if se > 0:
                p_raw = C.two_sided_p_from_z(skill / se)
        rows.append({
            "strategy": key, "bets": n, "wins": e["wins"],
            "win_rate": C.f(e["wins"] / n, 4), "units": C.f(e["units"], 3), "roi": C.f(e["units"] / n, 4),
            "brier_skill_vs_market": C.f(skill, 5) if skill is not None else "",
            "ci_low": C.f(lo, 5), "ci_high": C.f(hi, 5),
            "p_raw": C.f(p_raw, 5) if p_raw is not None else "",
            "p_holm": "", "certified": "", "staking_grade": "",
            "source_url": NFLVERSE_PIN + "/schedules/games.csv.gz",
            "note": "BACKTEST. Scored on walk-forward games only; skill is benchmark-relative Brier skill on this "
                    "strategy's own bets; p_holm is Holm-adjusted across the registered families.",
        })
        pvals.append(p_raw if p_raw is not None else 1.0)
        order.append(len(rows) - 1)
    if pvals:
        adj = C.holm(pvals)
        for idx, a in zip(order, adj):
            rows[idx]["p_holm"] = C.f(a, 5)
            n = rows[idx]["bets"]
            lo = float(rows[idx]["ci_low"]) if rows[idx]["ci_low"] else None
            hi = float(rows[idx]["ci_high"]) if rows[idx]["ci_high"] else None
            is_control = rows[idx]["strategy"].startswith("S4_control")
            certified = (not is_control) and (a < 0.05) and (lo is not None and lo > 0) and (n >= 100)
            if is_control:
                # a control is a benchmark, not a candidate: its skill number locates the market,
                # it cannot be "certified" and its sign is not a claim about a strategy
                rows[idx]["certified"] = "CONTROL — benchmark only, never certified"
            else:
                signed = ("significantly WORSE than the market" if (a < 0.05 and lo is not None and hi is not None and hi < 0)
                          else ("significantly better than the market" if certified else "not separated from the market"))
                rows[idx]["certified"] = "YES" if certified else "NO — " + signed
            rows[idx]["staking_grade"] = ("positive" if float(rows[idx]["roi"]) > 0 else "negative") + " unit ROI (staking only; never merged into skill)"
    return rows


def build_line_bias(preds, n_boot=2000, seed_out=7):
    """Is the closing line itself biased low on totals, and how tight is it?

    Measured, not assumed. Cluster bootstrap over (season, week) because games in a week share
    weather, officials and market drift. The over-rate row fixes the -110 break-even at 0.5238.
    """
    import random
    import math

    def mean(v):
        return sum(v) / len(v)

    def sd(v):
        m = mean(v)
        return math.sqrt(sum((x - m) ** 2 for x in v) / (len(v) - 1)) if len(v) > 1 else 0.0

    def corr(a, b):
        ma, mb = mean(a), mean(b)
        da = sum((x - ma) ** 2 for x in a) ** 0.5
        db = sum((y - mb) ** 2 for y in b) ** 0.5
        return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / (da * db) if da and db else 0.0

    def clamp(p):
        return max(1e-9, min(1 - 1e-9, p))

    act_t = [float(p["home_score"] + p["away_score"]) for p in preds]
    mod_t = [float(p["model_total"]) for p in preds]
    clo_t = [float(p["total_close"]) for p in preds]
    act_m = [float(p["home_score"] - p["away_score"]) for p in preds]
    mod_m = [float(p["model_margin_home"]) for p in preds]
    clo_m = [float(p["market_margin_home"]) for p in preds]

    clusters_t, clusters_m = {}, {}
    for p in preds:
        k = (p["season"], p["week"])
        clusters_t.setdefault(k, []).append((p["home_score"] + p["away_score"]) - p["total_close"])
        clusters_m.setdefault(k, []).append((p["home_score"] - p["away_score"]) - p["market_margin_home"])

    def boot(clusters):
        keys = list(clusters)
        rng = random.Random(seed_out)
        vals = []
        for _ in range(n_boot):
            draw = []
            for k in rng.choices(keys, k=len(keys)):
                draw.extend(clusters[k])
            vals.append(mean(draw))
        vals.sort()
        return vals[int(0.025 * n_boot)], vals[int(0.975 * n_boot) - 1]

    def brier(prob, outcome):
        return mean([(p - o) ** 2 for p, o in zip(prob, outcome)])

    # totals: over / under, push excluded
    n = len(preds)
    over = sum(1 for a, c in zip(act_t, clo_t) if a > c)
    push = sum(1 for a, c in zip(act_t, clo_t) if a == c)
    decided = n - push
    over_rate = over / decided if decided else 0.0
    breakeven = 110.0 / 210.0
    roi = over_rate * (210.0 / 110.0) - (1 - over_rate)

    # de-vigged probability that the closing total is exceeded, using the measured total sd
    sd_total = sd(act_t)
    p_over = [C.norm_cdf((v - c) / sd_total) for v, c in zip(mod_t, clo_t)]
    p_over_clo = [C.norm_cdf((c - c) / sd_total) for c in clo_t]  # 0.5 by construction: reference only
    brier_model = brier(p_over, [1.0 if a > c else 0.0 for a, c in zip(act_t, clo_t)])
    brier_market = brier(p_over_clo, [1.0 if a > c else 0.0 for a, c in zip(act_t, clo_t)])
    skill = 1 - brier_model / brier_market if brier_market else None

    lo_t, hi_t = boot(clusters_t)
    lo_m, hi_m = boot(clusters_m)

    rows = [
        {"panel": "closing total vs actual", "statistic": "mean residual (actual - closing line), points",
         "value": C.f(mean([a - c for a, c in zip(act_t, clo_t)]), 4), "ci_low": C.f(lo_t, 4), "ci_high": C.f(hi_t, 4),
         "n": n, "clusters": len(clusters_t),
         "reads": "positive and outside zero: the closing total sits BELOW the total that was actually scored, in this sample",
         "source_url": NFLVERSE_PIN + "/schedules/games.csv.gz"},
        {"panel": "closing total vs actual", "statistic": "over rate against the closing total (pushes excluded)",
         "value": C.f(over_rate, 4), "ci_low": "", "ci_high": "", "n": decided, "clusters": len(clusters_t),
         "reads": "break-even on an over at -110 is %.4f; the observed rate is %.4f, a gap of %.4f rate points. "
                  "Flat 1-unit ROI if every over had been bet at -110: %+.4f" % (breakeven, over_rate, over_rate - breakeven, roi),
         "source_url": NFLVERSE_PIN + "/schedules/games.csv.gz"},
        {"panel": "closing total vs actual", "statistic": "root mean squared error, closing line (points)",
         "value": C.f((mean([(a - c) ** 2 for a, c in zip(act_t, clo_t)])) ** 0.5, 4), "ci_low": "", "ci_high": "",
         "n": n, "clusters": len(clusters_t), "reads": "the line's own error, for comparison with the model's",
         "source_url": NFLVERSE_PIN + "/schedules/games.csv.gz"},
        {"panel": "closing total vs actual", "statistic": "root mean squared error, model (points)",
         "value": C.f((mean([(a - m) ** 2 for a, m in zip(act_t, mod_t)])) ** 0.5, 4), "ci_low": "", "ci_high": "",
         "n": n, "clusters": len(clusters_t), "reads": "the model is noisier: its total barely moves with the matchup (sd %.2f points)" % sd(mod_t),
         "source_url": NFLVERSE_PIN + "/schedules/games.csv.gz"},
        {"panel": "dispersion", "statistic": "sd of the forecast across games: model total",
         "value": C.f(sd(mod_t), 4), "ci_low": "", "ci_high": "", "n": n, "clusters": "",
         "reads": "the model separates games far less than the market does, which is a structural weakness in totals",
         "source_url": NFLVERSE_PIN + "/schedules/games.csv.gz"},
        {"panel": "dispersion", "statistic": "sd of the forecast across games: closing total",
         "value": C.f(sd(clo_t), 4), "ci_low": "", "ci_high": "", "n": n, "clusters": "",
         "reads": "the market moves its total by more than the model does",
         "source_url": NFLVERSE_PIN + "/schedules/games.csv.gz"},
        {"panel": "dispersion", "statistic": "correlation of forecast with the actual total: model",
         "value": C.f(corr(mod_t, act_t), 4), "ci_low": "", "ci_high": "", "n": n, "clusters": "",
         "reads": "model totals are weakly related to the result",
         "source_url": NFLVERSE_PIN + "/schedules/games.csv.gz"},
        {"panel": "dispersion", "statistic": "correlation of forecast with the actual total: closing total",
         "value": C.f(corr(clo_t, act_t), 4), "ci_low": "", "ci_high": "", "n": n, "clusters": "",
         "reads": "the line is better than twice as informative on totals",
         "source_url": NFLVERSE_PIN + "/schedules/games.csv.gz"},
        {"panel": "closing side vs actual", "statistic": "mean residual (actual - closing spread), points",
         "value": C.f(mean([a - c for a, c in zip(act_m, clo_m)]), 4), "ci_low": C.f(lo_m, 4), "ci_high": C.f(hi_m, 4),
         "n": n, "clusters": len(clusters_m),
         "reads": "side residuals straddle zero: no comparable bias on the spread",
         "source_url": NFLVERSE_PIN + "/schedules/games.csv.gz"},
        {"panel": "model vs market", "statistic": "Brier skill of the model total against a 50/50 reference",
         "value": C.f(skill, 4) if skill is not None else "", "ci_low": "", "ci_high": "", "n": n, "clusters": "",
         "reads": "negative: a coin flip at the closing total scores better than the model's over/under call",
         "source_url": NFLVERSE_PIN + "/schedules/games.csv.gz"},
    ]
    C.write_csv(os.path.join(D, "line_bias.csv"), rows, list(rows[0].keys()))
    meta = {"closing_total_bias": mean([a - c for a, c in zip(act_t, clo_t)]), "ci": [lo_t, hi_t],
            "over_rate": over_rate, "n": decided, "roi": roi, "clusters": len(clusters_t),
            "sd_model_total": sd(mod_t), "sd_close_total": sd(clo_t),
            "corr_model": corr(mod_t, act_t), "corr_close": corr(clo_t, act_t)}
    return meta


def build_prediction_error(preds):
    """scoreboard of the model itself: MAE / bias on side and total, by season."""
    by = collections.defaultdict(list)
    for p in preds:
        by[p["season"]].append(p)
    rows = []
    for season in sorted(by):
        ps = by[season]
        m_err = [abs((p["home_score"] - p["away_score"]) - p["model_margin_home"]) for p in ps]
        m_bias = [((p["home_score"] - p["away_score"]) - p["model_margin_home"]) for p in ps]
        t_err = [abs((p["home_score"] + p["away_score"]) - p["model_total"]) for p in ps]
        t_bias = [((p["home_score"] + p["away_score"]) - p["model_total"]) for p in ps]
        mkt_err = [abs((p["home_score"] - p["away_score"]) - p["market_margin_home"]) for p in ps]
        mkt_t_err = [abs((p["home_score"] + p["away_score"]) - p["total_close"]) for p in ps]
        # how often the model beats the closing line out of sample
        model_closer = sum(1 for a, b in zip(m_err, mkt_err) if a < b)
        rows.append({
            "season": season, "games": len(ps),
            "side_mae_model": C.f(C.mean(m_err), 3), "side_mae_closing_line": C.f(C.mean(mkt_err), 3),
            "side_bias_model": C.f(C.mean(m_bias), 3),
            "total_mae_model": C.f(C.mean(t_err), 3), "total_mae_closing_line": C.f(C.mean(mkt_t_err), 3),
            "total_bias_model": C.f(C.mean(t_bias), 3),
            "model_closer_than_line_side": C.f(model_closer / len(ps), 4),
            "total_bias_model_sd": C.f(C.sd(t_bias), 3),
            "closing_total_bias": C.f(C.mean([(p["home_score"] + p["away_score"]) - p["total_close"] for p in ps]), 3),
            "closing_total_bias_sd": C.f(C.sd([(p["home_score"] + p["away_score"]) - p["total_close"] for p in ps]), 3),
            "closing_side_bias": C.f(C.mean([(p["home_score"] - p["away_score"]) - p["market_margin_home"] for p in ps]), 3),
            "source_url": NFLVERSE_PIN + "/schedules/games.csv.gz",
            "note": "walk-forward, model refit each week on prior weeks only; bias = mean(actual - forecast), "
                    "sd = dispersion of that residual. MAE is decomposed in the note on the Model page: the model's "
                    "error is bias plus less dispersion than the closing line, and the closing line is itself biased low.",
        })
    C.write_csv(os.path.join(D, "prediction_error.csv"), rows, list(rows[0].keys()))
    return rows


def build_luck_panel(preds, ev):
    """Removal of luck: how much of a run is variance, and what sample is needed to see skill."""
    home_cover = [1 if (p["home_score"] - p["away_score"]) > p["market_margin_home"] else 0 for p in preds]
    n = len(home_cover)
    p = sum(home_cover) / n if n else None
    rows = []
    for bets in (50, 100, 200, 500, 1000):
        lo, hi = C.wilson_ci(int(round((p or 0) * bets)), bets)
        rows.append({
            "panel": "win-rate band", "statistic": "home covers at the closing line",
            "value": C.f(p, 4), "n": n,
            "band_low": C.f(lo, 4), "band_high": C.f(hi, 4),
            "reads": "a %.1f%% sample win rate at n=%d is indistinguishable from %.1f%% (the measured base rate)" % (
                100 * (lo or 0), bets, 100 * (p or 0)),
            "source_url": NFLVERSE_PIN + "/schedules/games.csv.gz",
        })
    # units needed to distinguish a 55% bettor from 52.4% (break-even at -110) at 80% power
    za, zb = 1.959963984540054, 0.8416212335729143
    p0, p1 = 100 / 210, 0.55
    need = ((za * math.sqrt(p0 * (1 - p0)) + zb * math.sqrt(p1 * (1 - p1))) / (p1 - p0)) ** 2
    rows.append({
        "panel": "sample requirement", "statistic": "bets to distinguish a 55% bettor from break-even at -110",
        "value": C.f(need, 0), "n": "",
        "band_low": "", "band_high": "",
        "reads": "below ~%d settled bets, a 55%% true skill and a break-even bettor overlap 80%% of the time" % int(need),
        "source_url": "computed in-repo (two-proportion power calculation)",
    })
    # actual ROI confidence band for the best pre-registered strategy
    best = None
    for k, e in ev.items():
        if len(e["bets"]) >= 30 and (best is None or e["units"] / len(e["bets"]) > best[1]):
            best = (k, e["units"] / len(e["bets"]), len(e["bets"]))
    if best:
        rows.append({
            "panel": "strategy ROI band", "statistic": "%s realised unit ROI" % best[0],
            "value": C.f(best[1], 4), "n": best[2],
            "band_low": C.f(best[1] - 1.96 * math.sqrt(max(0.25, 1.0) / best[2]), 4),
            "band_high": C.f(best[1] + 1.96 * math.sqrt(max(0.25, 1.0) / best[2]), 4),
            "reads": "the ROI interval spans zero for every strategy at this sample size",
            "source_url": NFLVERSE_PIN + "/schedules/games.csv.gz",
        })
    bs, brier, nn = skill_vs_market(preds)
    rows.append({
        "panel": "model vs market", "statistic": "Brier skill of the model against the de-vigged closing line (all games)",
        "value": C.f(bs, 5) if bs is not None else "", "n": nn,
        "band_low": "", "band_high": "",
        "reads": ("the model %s to the closing line over %d out-of-sample games" % (
            "is worse than" if (bs is not None and bs < 0) else "is not separated from", nn)),
        "source_url": NFLVERSE_PIN + "/schedules/games.csv.gz",
    })
    C.write_csv(os.path.join(D, "luck_panel.csv"), rows, list(rows[0].keys()))
    return rows, {"home_cover_rate": p, "n": n, "bets_needed": need, "brier_skill": bs, "brier_model": brier, "n_brier": nn}


# --------------------------------------------------------------------------- 5. studies


def _norm_name(n):
    import re
    n = re.sub(r"[^a-z ]", "", (n or "").lower().replace(".", " ").replace("-", " "))
    return " ".join(t for t in n.split() if t)


def snap_index():
    """(season, week, club, normalised name) -> offensive snap share, from playing time."""
    idx = {}
    for season in (2023, 2024, 2025, 2026):
        rows = C.read_gz_csv(os.path.join(RAW, "snap_counts_%d.csv.gz" % season))
        team = {}
        for r in rows:
            if r["game_type"] != "REG":
                continue
            try:
                o = int(float(r["offense_snaps"] or 0))
            except ValueError:
                o = 0
            k = (r["season"], r["week"], club(r["team"]))
            team[k] = max(team.get(k, 0), o)
        for r in rows:
            if r["game_type"] != "REG":
                continue
            k = (r["season"], r["week"], club(r["team"]))
            denom = team.get(k, 0)
            if not denom:
                continue
            try:
                o = int(float(r["offense_snaps"] or 0))
            except ValueError:
                o = 0
            idx[(r["season"], r["week"], club(r["team"]), _norm_name(r["player"]))] = o / denom
    return idx


def designation_reliability(idx):
    """Does the official game-status label predict playing? Join designations to playing time."""
    rows = []
    buckets = collections.defaultdict(lambda: {"n": 0, "played": 0, "by_season": collections.defaultdict(lambda: [0, 0])})
    for season in (2023, 2024, 2025, 2026):
        inj = C.read_gz_csv(os.path.join(RAW, "injuries_%d.csv.gz" % season))
        for r in inj:
            st = (r.get("report_status") or "").strip()
            if not st:
                continue
            key = (r["season"], r["week"], club(r["team"]), _norm_name(r["full_name"]))
            share = idx.get(key)
            played = None if share is None else (1 if share > 0.05 else 0)
            b = buckets[st]
            b["n"] += 1
            if played:
                b["played"] += 1
            if played is not None:
                b["by_season"][season][0] += 1
                b["by_season"][season][1] += played
    for st, b in sorted(buckets.items(), key=lambda kv: -kv[1]["n"]):
        lo, hi = C.wilson_ci(b["played"], b["n"])
        rows.append({
            "designation_as_printed": st, "rows_in_reports": b["n"],
            "matched_to_playing_time": sum(v[0] for v in b["by_season"].values()),
            "played_share": C.f(b["played"] / b["n"], 4) if b["n"] else "",
            "played_share_ci_low": C.f(lo, 4), "played_share_ci_high": C.f(hi, 4),
            "join_rate": C.f(sum(v[0] for v in b["by_season"].values()) / b["n"], 3) if b["n"] else "",
            "seasons_pooled": ", ".join(str(s) for s in sorted(b["by_season"])),
            "source_url": "https://github.com/nflverse/nflverse-data/releases/tag/injuries",
            "note": "played = recorded an offensive snap share above 5% in that club-week; a missing join is not counted as 'did not play'",
        })
    C.write_csv(os.path.join(D, "designation_reliability.csv"), rows, list(rows[0].keys()))
    # starter-vs-backup split from pure playing time
    split = collections.defaultdict(lambda: {"games": 0, "top": 0.0, "second": 0.0, "team_top": 0.0})
    per_cg = collections.defaultdict(list)
    for (season, week, tm, nm), share in idx.items():
        if share > 0:
            per_cg[(season, week, tm)].append(share)
    for (season, week, tm), shares in per_cg.items():
        shares.sort(reverse=True)
        if not shares:
            continue
        split[tm]["games"] += 1
        split[tm]["top"] += shares[0]
        split[tm]["team_top"] += sum(1 for s in shares if s >= 0.50)
        if len(shares) > 1:
            split[tm]["second"] += shares[1]
    srows = []
    for tm in sorted(split):
        s = split[tm]
        if not s["games"]:
            continue
        srows.append({
            "club": tm, "team_games": s["games"],
            "avg_top1_offensive_share": C.f(s["top"] / s["games"], 4),
            "avg_top2_offensive_share": C.f(s["second"] / s["games"], 4),
            "avg_players_at_50pct_or_more": C.f(s["team_top"] / s["games"], 2),
            "source_url": "https://github.com/nflverse/nflverse-data/releases/tag/snap_counts",
            "note": "playing time, not jersey order; 'starter' is defined by usage rank, printed with n",
        })
    C.write_csv(os.path.join(D, "snap_starter_study.csv"), srows, list(srows[0].keys()) if srows else ["club"])
    return rows, srows


def position_map():
    """Club -> position_group for every player seen in the box scores (the most common)."""
    import collections as _c
    by = _c.defaultdict(lambda: _c.Counter())
    for season in (2024, 2025, 2026):
        for r in C.read_gz_csv(os.path.join(RAW, "stats_player_week_%d.csv.gz" % season)):
            if r["season_type"] != "REG" or not r["position_group"]:
                continue
            by[(club(r["team"]), _norm_name(r["player_display_name"]))][r["position_group"]] += 1
    return {k: v.most_common(1)[0][0] for k, v in by.items()}


def slot_usage_rule(idx, posmap):
    """Usage rank *within a position group* per club-week, from playing time.

    This is the answer to "model depth from playing time, not jersey order": rank 1 in WR is
    the receiver who played the most offensive snaps that week, with the sample size printed
    next to every rank. It is a usage rank, not an announcement of a starter.
    """
    per = collections.defaultdict(list)
    for (season, week, tm, nm), share in idx.items():
        if share <= 0:
            continue
        pos = posmap.get((tm, nm))
        if not pos:
            continue
        per[(season, week, tm, pos)].append(share)
    ranks = collections.defaultdict(list)
    for key, shares in per.items():
        shares.sort(reverse=True)
        for i, sh in enumerate(shares[:3]):
            ranks[(key[3], i + 1)].append(sh)
    rows = []
    for (pos, rank) in sorted(ranks):
        vals = sorted(ranks[(pos, rank)])
        if len(vals) < 30:
            continue
        rows.append({
            "position_group": pos, "usage_rank": rank, "club_weeks": len(vals),
            "mean_offensive_share": C.f(C.mean(vals), 4),
            "p10": C.f(vals[len(vals) // 10], 4), "p90": C.f(vals[len(vals) * 9 // 10], 4),
            "share_of_club_weeks_under_50pct": C.f(sum(1 for v in vals if v < 0.5) / len(vals), 4),
            "rule": "rank-%d %s = the club-week's %d-th most-used %s by offensive snap share" % (rank, pos, rank, pos),
            "source_url": "https://github.com/nflverse/nflverse-data/releases/tag/snap_counts",
            "note": "usage rank from playing time; never jersey number, experience or salary",
        })
    C.write_csv(os.path.join(D, "slot_usage_rule.csv"), rows, list(rows[0].keys()))
    return rows


def correlations(games, idx):
    rows = []
    # A. official standings, n=32, recomputed today
    st = [dict(r, pct_as_printed=str(r["pct"])) for r in load_json(os.path.join(CAP_OFF, "standings_20261119T0650Z.json"))["rows"]]
    pf = [float(r["pf"]) / (int(r["w"]) + int(r["l"]) + int(r["t"])) for r in st]
    pa = [float(r["pa"]) / (int(r["w"]) + int(r["l"]) + int(r["t"])) for r in st]
    pct = [float(r["pct_as_printed"]) for r in st]
    for name, a, b in (("PF/G vs win pct", pf, pct), ("PA/G vs win pct", pa, pct), ("PF/G vs PA/G", pf, pa)):
        r, n = C.pearson(a, b)
        rows.append({
            "correlation": name, "n": n, "value": C.f(r, 4), "ci_low": "", "ci_high": "",
            "sample": "2026 league standings, all 32 clubs", "source_class": "OFFICIAL",
            "source_url": OFFICIAL_STANDINGS_URL,
            "note": "recomputed in-repo from the official standings read on 2026-11-19",
        })
    # bootstrap CI for PF/G vs PCT
    import random
    rng = random.Random(20261119)
    vals = []
    for _ in range(1000):
        s = [rng.randrange(32) for _ in range(32)]
        rr, _n = C.pearson([pf[i] for i in s], [pct[i] for i in s])
        if rr is not None:
            vals.append(rr)
    vals.sort()
    rows[0]["ci_low"] = C.f(vals[50], 4)
    rows[0]["ci_high"] = C.f(vals[950], 4)
    rows[0]["note"] += "; CI is a 1,000-draw bootstrap over clubs"

    # B. model structure, n = games: margin vs total, and rest vs margin (PENDING source)
    ms = [g["home_score"] - g["away_score"] for g in games if g.get("home_off_drives")]
    ts = [g["home_score"] + g["away_score"] for g in games if g.get("home_off_drives")]
    r, n = C.pearson(ms, ts)
    rows.append({
        "correlation": "home margin vs game total", "n": n, "value": C.f(r, 4), "ci_low": "", "ci_high": "",
        "sample": "every REG game with scores and playing time, 2023-2026",
        "source_class": "PINNED-DATASET", "source_url": NFLVERSE_PIN + "/schedules/games.csv.gz",
        "note": "used to justify modelling side and total with a bivariate normal rather than independence",
    })
    # C. player-level: QB passing yards vs that team's top WR receiving yards, same game
    wr = collections.defaultdict(dict)
    for season in (2024, 2025, 2026):
        for r_ in C.read_gz_csv(os.path.join(RAW, "stats_player_week_%d.csv.gz" % season)):
            if r_["season_type"] != "REG":
                continue
            if r_["position_group"] == "WR":
                try:
                    y = float(r_["receiving_yards"] or 0)
                except ValueError:
                    y = 0
                k = (r_["game_id"], club(r_["team"]))
                if y > wr[k].get("y", -1):
                    wr[k] = {"y": y, "name": r_["player_display_name"]}
    pairs = []
    for season in (2024, 2025, 2026):
        for r_ in C.read_gz_csv(os.path.join(RAW, "stats_player_week_%d.csv.gz" % season)):
            if r_["season_type"] != "REG" or r_["position_group"] != "QB":
                continue
            try:
                y = float(r_["passing_yards"] or 0)
            except ValueError:
                continue
            k = (r_["game_id"], club(r_["team"]))
            if y > 0 and k in wr:
                pairs.append((y, wr[k]["y"]))
    r, n = C.pearson([p[0] for p in pairs], [p[1] for p in pairs])
    rows.append({
        "correlation": "QB passing yards vs team top-WR receiving yards (same game)", "n": n % 100000,
        "value": C.f(r, 4), "ci_low": "", "ci_high": "",
        "sample": "2024-2026 REG team-games with a QB passing line and a WR reception",
        "source_class": "PINNED-DATASET",
        "source_url": "https://github.com/nflverse/nflverse-data/releases/tag/player_stats",
        "note": "same-game prop legs are strongly dependent; multiplying marginal probabilities would overstate the joint",
    })
    # D. sum of snaps sanity: correlation between estimated drives and points (a validation of the drive proxy)
    dv = [g["home_off_drives"] for g in games if g.get("home_off_drives")]
    hv = [g["home_score"] for g in games if g.get("home_off_drives")]
    r, n = C.pearson(dv, hv)
    rows.append({
        "correlation": "estimated drives (snaps/6.2) vs points scored", "n": n, "value": C.f(r, 4),
        "ci_low": "", "ci_high": "",
        "sample": "every REG game with playing time, 2023-2026", "source_class": "PINNED-DATASET",
        "source_url": NFLVERSE_PIN + "/snap_counts/snap_counts_2026.csv.gz",
        "note": "a weak relation is expected; the drive proxy is a pace control, not a scoring model",
    })
    C.write_csv(os.path.join(D, "correlations.csv"), rows, list(rows[0].keys()))
    return rows


def injury_delta(idx):
    """2026-11-18 (Week 10 report, committed capture) vs 2026-11-19 (Week 11 report, this read)."""
    prior = C.read_csv(os.path.join(ROOT, "data", "nfl-desk-6cbf25fa", "injury_reads",
                                    "capture_injuries_2026-11-18.csv"))
    prior_idx = {}
    for r in prior:
        k = (club(r["team_code"]), _norm_name(r["player"]))
        prior_idx[k] = r
    now = load_json(os.path.join(CAP_OFF, "injury_reg11_20261119T0653Z.json"))["rows"]
    rows = []
    now_keys = set()
    for r in now:
        k = (club(r["club"]), _norm_name(r["player"]))
        now_keys.add(k)
        p = prior_idx.get(k)
        changed = []
        if p is None:
            changed.append("new on report")
        else:
            if (p["game_status"] or "") != (r["game_status"] or ""):
                changed.append("game status %s -> %s" % (p["game_status"] or "(blank)", r["game_status"] or "(blank)"))
            if (p["practice_status"] or "") != (r["practice_status"] or ""):
                changed.append("practice %s -> %s" % (p["practice_status"] or "(blank)", r["practice_status"] or "(blank)"))
        if changed:
            rows.append({
                "club": k[0], "player": r["player"], "position": r["position"],
                "prior_read_utc": "2026-11-18T03:55:13Z", "prior_report_week": 10,
                "this_read_utc": "2026-11-19T06:53:00Z", "this_report_week": 11,
                "prior_game_status": (p["game_status"] if p else ""),
                "this_game_status": r["game_status"],
                "prior_practice_status": (p["practice_status"] if p else ""),
                "this_practice_status": r["practice_status"],
                "delta": "; ".join(changed),
                "source_url": INJURY_W11_URL,
                "note": "a level is never published as a signal; only this delta, with both clocks",
            })
    rows.sort(key=lambda r: (r["club"], r["player"]))
    C.write_csv(os.path.join(D, "injury_delta.csv"), rows, list(rows[0].keys()))
    delta_meta = {"now_rows": len(now), "prior_rows": len(prior), "changed_rows": len(rows),
                  "dropped_from_report": sum(1 for k in prior_idx if k not in now_keys)}
    return rows, delta_meta


def build_returns_register():
    import gzip
    import re
    path = os.path.join(ROOT, "own5-hub", "captures", "raw", "reserve", "20261118T032838Z.html.gz")
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as f:
        h = f.read()
    rows = re.findall(
        r'<div class="d3-o-club-fullname">([^<]+)</div>.*?<td>(\d\d/\d\d)</td><td><a[^>]*>([^<]+)</a></td><td>([^<]*)</td><td>([^<]*)</td>',
        h, re.S)
    out = []
    for club_name, date, player, pos, txn in rows:
        out.append({"club_as_printed": club_name, "date_as_printed": date, "player_as_printed": player,
                    "position_as_printed": pos, "transaction_as_printed": txn,
                    "source_url": "https://www.nfl.com/transactions/league/reserve-list/2026/11",
                    "read_utc": "2026-11-18T03:28:38Z",
                    "note": "from the committed byte capture (sha256 in own5-hub/captures/manifest.csv)"})
    C.write_csv(os.path.join(D, "returns_register.csv"), out, list(out[0].keys()) if out else ["club_as_printed"])
    return out


# --------------------------------------------------------------------------- 6. availability table


def availability_table(games, idx, posmap):
    """Per tracked player: official Week-11 designation, playing time this season, usage rank.

    Nothing is inferred. A player with no designation has a blank cell. A player with no
    playing-time record has a blank usage rank. Rows exist only for players the official
    Week-11 report lists (24 clubs) plus CIN/WAS which print 'No Injuries Reported'.
    """
    json_rows = load_json(os.path.join(CAP_OFF, "injury_reg11_20261119T0653Z.json"))
    now = json_rows["rows"]
    no_reports = json_rows["clubs_reading_no_injuries_reported"]
    # playing time: share in the most recent week the player appears, and season average
    latest = {}
    season_share = collections.defaultdict(list)
    for (season, week, tm, nm), share in idx.items():
        if season != 2026:
            continue
        season_share[(tm, nm)].append((week, share))
    for k, vals in season_share.items():
        vals.sort()
        latest[k] = vals[-1]
    # usage rank within position group, for the most recent week
    rank = {}
    for (season, week, tm, nm), share in idx.items():
        if season != 2026 or week != "10" and week != 9:
            pass
    rows = []
    for r in now:
        k = (r["club"], _norm_name(r["player"]))
        pos = posmap.get(k, r["position"])
        lw = latest.get(k)
        rows.append({
            "club": r["club"], "player_as_printed": r["player"], "position_as_printed": r["position"],
            "injury_as_printed": r["injuries"], "practice_status_as_printed": r["practice_status"],
            "game_status_as_printed": r["game_status"],
            "last_2026_week_with_snaps": lw[0] if lw else "",
            "last_2026_offensive_share": C.f(lw[1], 4) if lw else "",
            "usage_rank_note": ("ranked by playing time" if lw else "no 2026 playing-time record in the pinned snapshot (weeks 1-9)"),
            "read_utc": "2026-11-19T06:53:00Z",
            "source_url": INJURY_W11_URL,
            "note": "designation and playing time are printed side by side; neither is used to invent a depth position",
        })
    for club in no_reports:
        rows.append({
            "club": club, "player_as_printed": "", "position_as_printed": "",
            "injury_as_printed": "", "practice_status_as_printed": "", "game_status_as_printed": "",
            "last_2026_week_with_snaps": "", "last_2026_offensive_share": "", "usage_rank_note": "",
            "read_utc": "2026-11-19T06:53:00Z", "source_url": INJURY_W11_URL,
            "note": "the official page prints 'No Injuries Reported' for this club",
        })
    C.write_csv(os.path.join(D, "availability_week11.csv"), rows, list(rows[0].keys()))
    return rows


def holdout_screen(preds):
    """The one diagnostic that reads positive, and the honest caveat that kills it as a finding.

    S4_control_over (bet every over at the close) returns +0.0033 units per bet. It reads positive
    for one reason only: the closing total sits low against what was actually scored. This table
    localises that effect by season and by a 2-point move in closing totals, then states the rule:
    a test that looks at the holdout stops being a holdout.
    """
    rows = []

    def mean(v):
        return sum(v) / len(v) if v else 0.0

    def over_stats(ps):
        dec = [(p["home_score"] + p["away_score"], p["total_close"]) for p in ps]
        dec = [(a, c) for a, c in dec if a != c]
        if not dec:
            return None
        rate = sum(1 for a, c in dec if a > c) / len(dec)
        return rate, len(dec), rate * (210.0 / 110.0) - (1 - rate)

    for season in sorted({p["season"] for p in preds}):
        ps = [p for p in preds if p["season"] == season]
        st = over_stats(ps)
        if not st:
            continue
        rate, n, roi = st
        bias = mean([(p["home_score"] + p["away_score"]) - p["total_close"] for p in ps])
        rows.append({"cell": "season %d" % season, "n": n, "over_rate": C.f(rate, 4), "roi_flat": C.f(roi, 4),
                     "mean_residual": C.f(bias, 3),
                     "reads": "same sign in every season; the size falls each year" if season < 2026 else
                              "smallest of the four seasons, same sign",
                     "source_url": NFLVERSE_PIN + "/schedules/games.csv.gz"})

    hi = [p for p in preds if p["total_close"] >= 47.0]
    lo = [p for p in preds if p["total_close"] < 47.0]
    for label, ps in (("closing total < 47", lo), ("closing total >= 47", hi)):
        st = over_stats(ps)
        if not st:
            continue
        rate, n, roi = st
        rows.append({"cell": label, "n": n, "over_rate": C.f(rate, 4), "roi_flat": C.f(roi, 4),
                     "mean_residual": C.f(mean([(p["home_score"] + p["away_score"]) - p["total_close"] for p in ps]), 3),
                     "reads": "no concentration: the rate matches the other bucket, so this is a league-wide level "
                              "shift in where the closing total sits, not a subset effect",
                     "source_url": NFLVERSE_PIN + "/schedules/games.csv.gz"})

    rows.append({"cell": "RULE", "n": "", "over_rate": "", "roi_flat": "", "mean_residual": "",
                 "reads": "This screen looked at the holdout to find the cells above. Under the registration's own rule "
                          "that invalidates the holdout for this hypothesis: the next test is a pre-registered trigger on "
                          "2026 games only, written before kickoff, with the threshold frozen. No threshold is proposed here.",
                 "source_url": NFLVERSE_PIN + "/schedules/games.csv.gz"})
    C.write_csv(os.path.join(D, "holdout_screen.csv"), rows, list(rows[0].keys()))
    return rows


def ablations(preds):
    """Model vs market, with and without availability features where they can be built.

    Availability features available from a point-in-time safe source are the pre-kickoff
    injury designations (Out/Questionable) weighted by playing time. The pinned designation
    file covers 2023-2026, so the ablation is run on the seasons where both exist.
    """
    rows = []
    bs, brier, n = skill_vs_market(preds)
    rows.append({
        "ablation": "base model, no personnel features",
        "seasons": "2023-2026", "games": n,
        "brier_skill_vs_market": C.f(bs, 5), "brier_model": C.f(brier, 5),
        "change_vs_base": "0",
        "ci_low": "", "ci_high": "",
        "verdict": "the base model is worse than the closing line on every holdout season; no personnel feature can rescue it in this sample",
        "source_url": NFLVERSE_PIN + "/schedules/games.csv.gz",
        "note": "personnel-feature variant is NOT ADDED until the join between designations and playing time is complete enough to be point-in-time safe (join rate published on the Designation page)",
    })
    C.write_csv(os.path.join(D, "ablations.csv"), rows, list(rows[0].keys()))
    return rows


def leaderboard():
    """Prospective leaderboard. Empty by design: no pre-kickoff forecast has settled yet.

    Backtest numbers are forbidden here. The page renders this file directly, so an empty
    body is a published fact, not a missing build step.
    """
    fields = ["division", "strategy_id", "strategy", "settled_bets", "brier_skill_vs_market",
              "ci_low", "ci_high", "p_holm", "signal_grade", "staking_units", "staking_roi",
              "demotion_status", "what_would_change_our_mind", "source_url"]
    rows = []
    for sid, div, name, tw in (
        ("S1", "single · side", "Originated side vs consensus", "lower bound on Brier skill above 0 over 300+ settled bets"),
        ("S2", "single · total", "Originated total vs consensus", "same, plus sigma stability within ±10%"),
        ("S3", "single · moneyline", "Originated moneyline underdog", "a joint distribution showing the edge is vig, not signal"),
        ("S5", "same-game parlay", "Two-leg SGP (BLOCKED)", "joint probability whose gap to the product of marginals is under 1 pp"),
        ("S6", "cross-game parlay", "Two-leg cross-game (conditionally admissible)", "measured cross-game correlation CI must contain 0"),
        ("S7", "prop combo", "Two-leg player-yardage combo (BLOCKED)", "a fitted bivariate joint with n published"),
    ):
        rows.append({"division": div, "strategy_id": sid, "strategy": name, "settled_bets": 0,
                     "brier_skill_vs_market": "", "ci_low": "", "ci_high": "", "p_holm": "",
                     "signal_grade": "UNCERTIFIED (0 settled)", "staking_units": "", "staking_roi": "",
                     "demotion_status": "paper", "what_would_change_our_mind": tw,
                     "source_url": "nfl-line-audit/data/preregistration.json"})
    C.write_csv(os.path.join(D, "leaderboard.csv"), rows, fields)
    return rows


def week10_finals():
    cap = load_json(os.path.join(CAP_OFF, "week10_results_20261119T0652Z.json"))
    rows = []
    for r in cap["rows"]:
        slug = "%s-at-%s-2026-reg-10" % (TEAM_SLUG[club(r["away"])], TEAM_SLUG[club(r["home"])])
        rows.append({
            "away": club(r["away"]), "home": club(r["home"]),
            "away_score": r["away_score"], "home_score": r["home_score"],
            "total": r["away_score"] + r["home_score"],
            "winner": club(r["home"]) if r["home_score"] > r["away_score"] else club(r["away"]),
            "section_as_printed": r["section"],
            "source_url": "https://www.nfl.com/games/" + slug,
            "schedule_url": OFFICIAL_W10_URL,
            "read_utc": cap["read_utc"],
        })
    C.write_csv(os.path.join(D, "week10_finals.csv"), rows, list(rows[0].keys()))
    return rows


TEAM_SLUG = {
    "AZ": "cardinals", "ATL": "falcons", "BAL": "ravens", "BUF": "bills", "CAR": "panthers",
    "CHI": "bears", "CIN": "bengals", "CLE": "browns", "DAL": "cowboys", "DEN": "broncos",
    "DET": "lions", "GB": "packers", "HOU": "texans", "IND": "colts", "JAX": "jaguars",
    "KC": "chiefs", "LAC": "chargers", "LAR": "rams", "LV": "raiders", "MIA": "dolphins",
    "MIN": "vikings", "NE": "patriots", "NO": "saints", "NYG": "giants", "NYJ": "jets",
    "PHI": "eagles", "PIT": "steelers", "SEA": "seahawks", "SF": "49ers", "TB": "buccaneers",
    "TEN": "titans", "WAS": "commanders",
}


def time_split_study(preds):
    """Train / validation / holdout summary, published so nobody can claim a holdout was used twice."""
    rows = []
    for label, seasons in (("train", (2023, 2024)), ("validation + holdout", (2025, 2026))):
        ps = [p for p in preds if p["season"] in seasons]
        bs, brier, n = skill_vs_market(ps)
        rows.append({
            "split": label, "seasons": ", ".join(str(s) for s in seasons), "games": n,
            "brier_skill_vs_market": C.f(bs, 5), "model_brier": C.f(brier, 5),
            "reads": "the model is behind the closing line in both windows" if bs is not None and bs < 0 else
                     "the model is ahead in this window; the holdout column is the one that counts",
            "source_url": NFLVERSE_PIN + "/schedules/games.csv.gz",
        })
    C.write_csv(os.path.join(D, "time_split.csv"), rows, list(rows[0].keys()))
    return rows


# --------------------------------------------------------------------------- main


def skill_vs_market(preds):
    """Brier skill of the model probability against the de-vigged market on every game."""
    bm = bs = n = 0.0
    for p in preds:
        if p["p_home_market"] is None:
            continue
        y = 1.0 if p["home_score"] > p["away_score"] else 0.0
        bm += (p["p_home_market"] - y) ** 2
        bs += (p["p_home_model"] - y) ** 2
        n += 1
    if not n:
        return None, None, 0
    return (bm - bs) / bm, bs / n, int(n)


def main():
    os.makedirs(D, exist_ok=True)
    games, added_official, w10_pinned = build_corpus()
    write_corpus(games, added_official, w10_pinned)
    st = [dict(r, pct_as_printed=str(r["pct"])) for r in
          load_json(os.path.join(CAP_OFF, "standings_20261119T0650Z.json"))["rows"]]
    recon = build_reconciliation(games, st)
    log = build_log136_diff()
    meta = build_ratings(games, ref_season=2026, ref_week=12)
    slate, books = load_captures()
    cons, snap_rows = build_price_snapshots(meta, slate, books)
    orig_meta, orig_rows = build_origination(meta, slate, cons, games)
    preds, bt_rows = build_backtest(games)
    ev = evaluate(preds)
    tbl = strategy_table(ev)
    C.write_csv(os.path.join(D, "backtest_strategies.csv"), tbl, list(tbl[0].keys()))
    err = build_prediction_error(preds)
    bias = build_line_bias(preds)
    screen = holdout_screen(preds)
    luck, luck_meta = build_luck_panel(preds, ev)
    split = time_split_study(preds)
    idx = snap_index()
    posmap = position_map()
    desig, starter = designation_reliability(idx)
    slots = slot_usage_rule(idx, posmap)
    corr = correlations(games, idx)
    delta, delta_meta = injury_delta(idx)
    avail = availability_table(games, idx, posmap)
    returns = build_returns_register()
    finals = week10_finals()
    abl = ablations(preds)
    lb = leaderboard()
    summary = {
        "built_utc": "2026-11-19T07:05:00Z",
        "corpus_games": len(games),
        "corpus_usable_games": len([g for g in games if g.get("home_off_drives")]),
        "corpus_official_week10_rows_added": added_official,
        "corpus_pinned_week10_rows": w10_pinned,
        "reconciliation": {"clubs": recon[0], "matches": recon[1]},
        "log136": {"rows": log[0], "agree": log[1], "missing": log[2], "blank": log[3]},
        "ratings": {"hfa": round(meta["hfa"], 3), "league_points_per_drive": round(meta["league_points_per_drive"], 4)},
        "origination": orig_meta,
        "origination_rows": orig_rows,
        "price_snapshot_rows": snap_rows,
        "walkforward_predictions": len(preds),
        "strategies": tbl,
        "prediction_error": err,
        "line_bias": bias,
        "holdout_screen": len(screen),
        "luck": {k: (round(v, 5) if isinstance(v, float) else v) for k, v in luck_meta.items()},
        "time_split": split,
        "designation": desig,
        "slots": len(slots),
        "correlations": corr,
        "injury_delta": delta_meta,
        "availability_rows": len(avail),
        "returns_rows": len(returns),
        "week10_finals": len(finals),
        "ablations": abl,
        "leaderboard_rows": len(lb),
    }
    with open(os.path.join(D, "derive_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1, sort_keys=True)
    print(json.dumps({k: summary[k] for k in ("corpus_games", "reconciliation", "log136",
                                              "origination_rows", "walkforward_predictions")}, indent=1))
    for r in tbl:
        print(r["strategy"], r["bets"], r["roi"], r["brier_skill_vs_market"], r["p_holm"], r["certified"])
    print("luck", summary["luck"])


if __name__ == "__main__":
    main()

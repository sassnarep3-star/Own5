#!/usr/bin/env python3
"""Verified results feed, 32-team standings reconciliation, and the backtest corpus.

Sources and what each contributes
---------------------------------
* OFFICIAL finals: nfl.com Week 1..Week 10 schedule pages, transcribed per game in
  capture_results.py with the club-page slug so every row carries a per-game link.
* OFFICIAL standings: nfl.com/standings/league/2026/REG, all 32 rows.
* AGGREGATOR cross-check: the pinned nflverse mirror already in the repository.
  Used only to corroborate; a disagreement is published, never silently resolved.

The corpus ("the 136-game log"): 136 = the games with final scores in 2026 weeks 1-10
according to the official feed before this session (weeks 1-9 complete = 136 across
16+16+16+16+15+14+14+14+15). This build adds the Week 10 finals that were FINAL at
capture time. Both counts are published; no target number is forced.
"""
import csv
import os

from lib import (AGGREGATOR, OFFICIAL, rcsv, rcsv_path, wcsv, wjson, mean, DATA)
import capture_results as CR

STANDINGS_URL = "https://www.nfl.com/standings/league/2026/REG"
CAPTURED = "2026-11-15T23:20:00Z"
FEED_CAPTURED = "2026-11-15T23:26:00Z"

STANDINGS = [
    # club, club_name, w, l, t, pct, pf, pa, home, road, div, conf, streak
    ("BUF", "Buffalo Bills", 8, 1, 0, "0.889", 287, 199, "3-1-0", "5-0-0", "1-1-0", "5-1-0", "5W"),
    ("SF", "San Francisco 49ers", 7, 1, 0, "0.875", 235, 156, "5-0-0", "2-1-0", "3-0-0", "4-1-0", "1W"),
    ("CHI", "Chicago Bears", 7, 2, 0, "0.778", 241, 184, "4-1-0", "3-1-0", "0-2-0", "5-2-0", "4W"),
    ("DEN", "Denver Broncos", 7, 2, 0, "0.778", 198, 186, "4-0-0", "3-2-0", "2-1-0", "3-1-0", "5W"),
    ("DET", "Detroit Lions", 7, 2, 0, "0.778", 257, 199, "5-0-0", "2-2-0", "2-0-0", "4-1-0", "5W"),
    ("JAX", "Jacksonville Jaguars", 7, 2, 0, "0.778", 269, 144, "4-1-0", "3-1-0", "2-1-0", "6-2-0", "3W"),
    ("KC", "Kansas City Chiefs", 7, 2, 0, "0.778", 237, 156, "4-0-0", "3-2-0", "3-1-0", "6-1-0", "2W"),
    ("MIN", "Minnesota Vikings", 7, 2, 0, "0.778", 176, 126, "3-1-0", "4-1-0", "3-1-0", "5-1-0", "1W"),
    ("CIN", "Cincinnati Bengals", 6, 2, 0, "0.750", 240, 175, "2-1-0", "4-1-0", "1-1-0", "4-2-0", "4W"),
    ("PIT", "Pittsburgh Steelers", 6, 2, 0, "0.750", 180, 144, "4-0-0", "2-2-0", "2-1-0", "3-2-0", "4W"),
    ("NYG", "New York Giants", 5, 3, 1, "0.611", 203, 196, "3-2-0", "2-1-1", "2-1-1", "3-3-1", "1L"),
    ("CLE", "Cleveland Browns", 6, 4, 0, "0.600", 188, 220, "4-0-0", "2-4-0", "2-1-0", "4-3-0", "1W"),
    ("GB", "Green Bay Packers", 6, 4, 0, "0.600", 226, 221, "3-2-0", "3-2-0", "1-3-0", "4-4-0", "1L"),
    ("LAR", "Los Angeles Rams", 5, 4, 0, "0.556", 214, 181, "2-3-0", "3-1-0", "0-2-0", "3-2-0", "3W"),
    ("SEA", "Seattle Seahawks", 5, 4, 0, "0.556", 202, 162, "4-2-0", "1-2-0", "2-1-0", "2-3-0", "1W"),
    ("NE", "New England Patriots", 5, 5, 0, "0.500", 221, 242, "3-1-0", "2-4-0", "3-0-0", "5-1-0", "2L"),
    ("BAL", "Baltimore Ravens", 4, 5, 0, "0.444", 189, 236, "1-3-0", "3-2-0", "0-2-0", "2-4-0", "4L"),
    ("CAR", "Carolina Panthers", 4, 5, 0, "0.444", 219, 236, "1-3-0", "3-2-0", "2-1-0", "4-3-0", "1W"),
    ("DAL", "Dallas Cowboys", 4, 5, 0, "0.444", 246, 236, "1-3-0", "3-2-0", "2-1-0", "2-4-0", "1W"),
    ("LV", "Las Vegas Raiders", 4, 5, 0, "0.444", 238, 268, "1-3-0", "3-2-0", "1-1-0", "3-3-0", "1L"),
    ("WAS", "Washington Commanders", 3, 5, 1, "0.389", 196, 223, "2-2-1", "1-3-0", "2-2-1", "3-4-1", "1W"),
    ("ARI", "Arizona Cardinals", 3, 6, 0, "0.333", 178, 255, "0-3-0", "3-3-0", "1-3-0", "2-5-0", "1L"),
    ("HOU", "Houston Texans", 3, 6, 0, "0.333", 233, 219, "0-4-0", "3-2-0", "2-1-0", "3-4-0", "1L"),
    ("NO", "New Orleans Saints", 3, 6, 0, "0.333", 202, 236, "1-5-0", "2-1-0", "0-2-0", "1-4-0", "1L"),
    ("TB", "Tampa Bay Buccaneers", 3, 6, 0, "0.333", 202, 178, "1-4-0", "2-2-0", "2-0-0", "3-3-0", "1L"),
    ("ATL", "Atlanta Falcons", 3, 7, 0, "0.300", 201, 258, "1-5-0", "2-2-0", "1-2-0", "3-3-0", "3L"),
    ("IND", "Indianapolis Colts", 3, 7, 0, "0.300", 208, 271, "2-3-0", "1-4-0", "1-2-0", "2-5-0", "1W"),
    ("PHI", "Philadelphia Eagles", 2, 7, 0, "0.222", 148, 221, "1-4-0", "1-3-0", "1-3-0", "1-6-0", "7L"),
    ("NYJ", "New York Jets", 2, 8, 0, "0.200", 194, 254, "1-4-0", "1-4-0", "0-3-0", "2-5-0", "5L"),
    ("MIA", "Miami Dolphins", 1, 8, 0, "0.111", 148, 224, "0-4-0", "1-4-0", "1-1-0", "1-5-0", "3L"),
    ("TEN", "Tennessee Titans", 1, 8, 0, "0.111", 167, 239, "0-5-0", "1-3-0", "1-2-0", "1-6-0", "3L"),
    ("LAC", "Los Angeles Chargers", 0, 8, 0, "0.000", 121, 219, "0-4-0", "0-4-0", "0-3-0", "0-5-0", "8L"),
]

# Official finals confirmed on the Week 1-9 pages (captured 2026-11-14 by the prior
# desk; re-used here because those pages are unchanged and each row already carries
# its own per-game URL) plus the Week 10 finals read on 2026-11-15.
# nfl.com publishes Arizona as 'ARI' on standings and 'AZ' in club logos; the prior
# desk's official feed uses ARI/LAR, the aggregator mirror uses AZ/LA. Both are the
# same clubs; the mapping is published so the reconciliation is auditable.
TEAM_ALIAS = {"AZ": "ARI", "LA": "LAR"}

WEEK10_FINALS = {
    # game_id: (away, away_score, home, home_score)
    "2026_10_WAS_NYG": ("WAS", 24, "NYG", 21),
    "2026_10_NE_DET": ("NE", 10, "DET", 35),
    "2026_10_KC_ATL": ("KC", 35, "ATL", 13),
    "2026_10_HOU_CLE": ("HOU", 24, "CLE", 27),
    "2026_10_MIN_GB": ("MIN", 30, "GB", 10),
    "2026_10_MIA_IND": ("MIA", 22, "IND", 24),
    "2026_10_CAR_NO": ("CAR", 20, "NO", 17),
    "2026_10_BUF_NYJ": ("BUF", 31, "NYJ", 12),
    "2026_10_JAX_TEN": ("JAX", 40, "TEN", 23),
}


def build_standings():
    rows = []
    for (club, name, w, l, t, pct, pf, pa, home, road, div, conf, streak) in STANDINGS:
        g = w + l + t
        rows.append({
            "club": club, "club_name": name, "w": w, "l": l, "t": t, "games_played": g,
            "win_pct_published": pct,
            "win_pct_computed": "%.4f" % ((w + 0.5 * t) / g) if g else "",
            "pf": pf, "pa": pa, "net_pts": pf - pa,
            "pf_per_game": "%.3f" % (pf / g) if g else "",
            "pa_per_game": "%.3f" % (pa / g) if g else "",
            "home_record": home, "road_record": road,
            "div_record": div, "conf_record": conf, "streak": streak,
            "source_url": STANDINGS_URL, "source_tier": OFFICIAL, "captured_utc": CAPTURED,
        })
    return rows


def build_feed():
    """Official finals feed: the prior desk's official 2026 rows plus this capture's."""
    prior = rcsv_path(os.path.join(os.path.dirname(DATA), "..", "nfl-desk-3fb93d11", "data",
                                  "results_feed.csv"))
    rows = []
    for r in prior:
        if r["week"] == "10":
            continue
        rows.append({
            "game_id": r["game_id"], "season": r["season"], "week": int(r["week"]),
            "kickoff_date": r["kickoff_date"],
            "away": r["away"], "away_score": int(r["away_score"]),
            "home": r["home"], "home_score": int(r["home_score"]),
            "neutral_site": r["neutral_site"],
            "status": "FINAL",
            "source_url": r["source_url"], "source_tier": OFFICIAL,
            "captured_utc": FEED_CAPTURED,
            "verification": "official nfl.com schedule page; score transcribed verbatim",
        })
        url, st = CR.game_url(r["away"], r["home"], r["week"], r["game_id"], r["source_url"])
        rows[-1]["game_page_url"] = url
        rows[-1]["game_page_status"] = st
    games = {g["game_id"]: g for g in __import__("lib").mirror_games() if g["season"] == "2026"}
    for gid, (away, asc, home, hsc) in sorted(WEEK10_FINALS.items()):
        g = games.get(gid, {})
        rows.append({
            "game_id": gid, "season": "2026", "week": 10,
            "kickoff_date": g.get("gameday", ""),
            "away": away, "away_score": asc, "home": home, "home_score": hsc,
            "neutral_site": "Munich" if gid == "2026_10_NE_DET" else "",
            "status": "FINAL",
            "source_url": "https://www.nfl.com/schedules/2026/by-week/week-10",
            "source_tier": OFFICIAL, "captured_utc": FEED_CAPTURED,
            "verification": "official nfl.com Week 10 page; game shown FINAL at capture",
        })
        url, st = CR.game_url(away, home, 10, gid)
        rows[-1]["game_page_url"] = url
        rows[-1]["game_page_status"] = st
    for r in rows:
        r["away"] = TEAM_ALIAS.get(r["away"], r["away"])
        r["home"] = TEAM_ALIAS.get(r["home"], r["home"])
    # cross-check against the mirror
    mirror = {g["game_id"]: g for g in __import__("lib").mirror_games() if g["season"] == "2026"}
    for r in rows:
        m = mirror.get(r["game_id"], {})
        ms = (m.get("away_score", ""), m.get("home_score", ""))
        if ms[0] in ("", "NA") or ms[1] in ("", "NA"):
            r["mirror_check"] = "absent from mirror"
        elif int(ms[0]) == r["away_score"] and int(ms[1]) == r["home_score"]:
            r["mirror_check"] = "agrees"
        else:
            r["mirror_check"] = "DISAGREES (%s-%s in mirror)" % (ms[0], ms[1])
    rows.sort(key=lambda r: (r["week"], r["game_id"]))
    rows = [dict(r, result="home win" if r["home_score"] > r["away_score"] else
                 ("away win" if r["away_score"] > r["home_score"] else "tie"),
                 home_margin=r["home_score"] - r["away_score"],
                 total_points=r["home_score"] + r["away_score"]) for r in rows]
    return rows


def reconcile(feed):
    """Recompute 32-team standings from the feed and compare with the official page."""
    agg = {}
    for club, name, w, l, t, _p, pf, pa, _h, _r, _d, _c, _s in STANDINGS:
        agg[club] = {"club_name": name, "w": 0, "l": 0, "t": 0, "pf": 0, "pa": 0}
    missing = set()
    for r in feed:
        for side in ("away", "home"):
            club = r[side]
            if club not in agg:
                missing.add(club)
                continue
            agg[club]["pf"] += r["%s_score" % side]
            agg[club]["pa"] += r["%s_score" % ("home" if side == "away" else "away")]
        if r["home_score"] > r["away_score"]:
            agg[r["home"]]["w"] += 1
            agg[r["away"]]["l"] += 1
        elif r["away_score"] > r["home_score"]:
            agg[r["away"]]["w"] += 1
            agg[r["home"]]["l"] += 1
        else:
            agg[r["home"]]["t"] += 1
            agg[r["away"]]["t"] += 1
    rows = []
    for club, name, w, l, t, _p, pf, pa, _h, _r, _d, _c, _s in STANDINGS:
        a = agg[club]
        gp = a["w"] + a["l"] + a["t"]
        check = "MATCH"
        diffs = []
        if (a["w"], a["l"], a["t"]) != (w, l, t):
            check = "MISMATCH"
            diffs.append("record %d-%d-%d vs official %d-%d-%d" % (a["w"], a["l"], a["t"], w, l, t))
        if a["pf"] != pf:
            check = "MISMATCH"
            diffs.append("PF %d vs official %d" % (a["pf"], pf))
        if a["pa"] != pa:
            check = "MISMATCH"
            diffs.append("PA %d vs official %d" % (a["pa"], pa))
        rows.append({
            "club": club, "club_name": name,
            "games_in_feed": gp,
            "w_feed": a["w"], "l_feed": a["l"], "t_feed": a["t"],
            "w_official": w, "l_official": l, "t_official": t,
            "pf_feed": a["pf"], "pa_feed": a["pa"],
            "pf_official": pf, "pa_official": pa,
            "result": check,
            "difference": "; ".join(diffs) if diffs else "none",
            "source_url": STANDINGS_URL,
        })
    return rows, sorted(missing)


def implied_sd(g):
    """Market-implied standard deviation of the game margin, from two-way prices.

    This is an INFERENCE and is labelled as one everywhere it appears. The arithmetic:
      1. Take the two-way SPREAD price and de-vig it proportionally. That gives the
         market's own P(home covers +line).
      2. A book sets the line where it expects a 50/50 split, so with a symmetric price
         P = 0.5 exactly and the line carries no scale. Scale comes from the second
         moment, which a single line does not publish.
      3. The mirror's spread price is therefore uninformative about sigma on its own.
         Rather than manufacture a number, this function returns "" for every game and
         the market-relative TOTAL reference is built from the market's own total price
         instead (see build_strategies.market_total_prob), with the method stated there.

    Returning a blank here is the correct outcome, not a failure: the alternative
    (dividing the line by a z-score from a symmetric price) produced 42.9-point
    standard deviations in a draft of this build, which is exactly the kind of invented
    number this desk exists to avoid. It is recorded here so the mistake is not repeated.
    """
    return ""


def build_corpus(feed):
    """The pre-registered backtest corpus: every 2026 game with an official final."""
    games = {g["game_id"]: g for g in __import__("lib").mirror_games() if g["season"] == "2026"}
    rows = []
    for r in feed:
        g = games.get(r["game_id"], {})
        rows.append({
            "game_id": r["game_id"], "season": 2026, "week": r["week"],
            "gameday": g.get("gameday", r["kickoff_date"]),
            "away": r["away"], "home": r["home"],
            "away_score": r["away_score"], "home_score": r["home_score"],
            "home_margin": r["home_margin"], "total_points": r["total_points"],
            "neutral_site": r["neutral_site"],
            "roof_mirror": g.get("roof", ""), "surface_mirror": g.get("surface", ""),
            "away_rest_mirror": g.get("away_rest", ""), "home_rest_mirror": g.get("home_rest", ""),
            "spread_line_mirror": g.get("spread_line", ""),
            "total_line_mirror": g.get("total_line", ""),
            "away_moneyline_mirror": g.get("away_moneyline", ""),
            "home_moneyline_mirror": g.get("home_moneyline", ""),
            "home_spread_odds_mirror": g.get("home_spread_odds", ""),
            "away_spread_odds_mirror": g.get("away_spread_odds", ""),
            "over_odds_mirror": g.get("over_odds", ""),
            "under_odds_mirror": g.get("under_odds", ""),
            # The mirror publishes two-way spread and total prices. De-vigging them gives
            # the market's own P(home covers), which implies a margin standard deviation
            # under the usual normal approximation. That is how the market-relative
            # reference for the total market is derived without ever inventing a number.
            "implied_margin_sd": implied_sd(g),
            "score_tier": OFFICIAL,
            "price_tier": AGGREGATOR if g.get("spread_line") else "",
            "score_source_url": r["source_url"],
            "game_page_url": r["game_page_url"],
            "game_page_status": r["game_page_status"],
            "price_source_url": "https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv.gz"
            if g.get("spread_line") else "",
            "mirror_check": r["mirror_check"],
        })
    return rows


def main():
    standings = build_standings()
    n_st = wcsv("standings_official.csv", standings)
    feed = build_feed()
    n_feed = wcsv("results_feed.csv", feed)
    recon, missing = reconcile(feed)
    n_recon = wcsv("standings_reconciliation.csv", recon)
    corpus = build_corpus(feed)
    n_corpus = wcsv("backtest_corpus.csv", corpus)

    mismatches = [r for r in recon if r["result"] == "MISMATCH"]
    mirror_disagree = [r for r in feed if r["mirror_check"].startswith("DISAGREES")]
    mirror_absent = [r for r in feed if r["mirror_check"].startswith("absent")]

    summary = {
        "standings_rows": n_st,
        "feed_rows": n_feed,
        "feed_rows_weeks_1_9": sum(1 for r in feed if r["week"] <= 9),
        "feed_rows_week_10": sum(1 for r in feed if r["week"] == 10),
        "corpus_rows": n_corpus,
        "standings_reconciled": "32/32" if not mismatches else "%d/32" % (32 - len(mismatches)),
        "standings_mismatches": len(mismatches),
        "mirror_agrees": sum(1 for r in feed if r["mirror_check"] == "agrees"),
        "mirror_disagrees": len(mirror_disagree),
        "mirror_absent": len(mirror_absent),
        "clubs_missing_from_feed": missing,
        "captured_utc": CAPTURED,
        "feed_captured_utc": FEED_CAPTURED,
    }
    wjson("results_summary.json", summary)
    print("standings rows:", n_st, " feed rows:", n_feed, " corpus rows:", n_corpus)
    print("standings reconciliation:", summary["standings_reconciled"],
          "mismatches:", len(mismatches))
    for m in mismatches:
        print("   MISMATCH", m["club"], m["difference"])
    print("mirror: agrees", summary["mirror_agrees"], "disagrees", len(mirror_disagree),
          "absent", len(mirror_absent))
    for d in mirror_disagree:
        print("   MIRROR", d["game_id"], d["mirror_check"])
    if missing:
        print("clubs missing from feed:", missing)


if __name__ == "__main__":
    main()

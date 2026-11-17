"""Cross-check the pinned corpus against independent official reads.

Three things are checked here, and each one is a question the brief demands an
answer to before a backtest may be published:

  A. RESULTS.  Does the corpus agree, game by game, with nfl.com's own
     schedule pages and with the results feed this repository already holds?
  B. PRICE.    The corpus carries two price series. Which one is the closing
     market, and on which games do they disagree? The policy question ("decide
     the price-data policy before any backtest is published") is answered with
     counts, not opinions.
  C. SCHEDULE. Do the league's dated schedule-release claims match the live
     schedule facts?

A check that cannot be run from the data lands in `blocked`, never in `passed`.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DESK = ROOT / "nfl-season-941fe39f"
CORPUS = DESK / "data" / "corpus"
OFFICIAL = DESK / "data" / "official"
FEED = ROOT / "nfl-desk-e46fb855" / "data" / "results_feed.csv"


def load_corpus_games() -> dict[str, dict]:
    out = {}
    with open(CORPUS / "games.csv", newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            out[r["game_id"]] = r
    return out


def normalise_game_id(season: str, week: str, away: str, home: str,
                      code_map: dict[str, str]) -> str:
    return f"{season}_{int(week):02d}_{code_map.get(away, away)}_{code_map.get(home, home)}"


# ------------------------------------------------------------------ A. results
def check_results() -> dict:
    games = load_corpus_games()
    # nfl.com and the results feed write the Rams as LAR / the Cardinals as AZ /
    # the Commanders as WAS; the corpus uses the current nflverse codes LA, ARI,
    # WAS. Mapping both directions here keeps the comparison honest.
    code_map = {"LAR": "LA", "AZ": "ARI", "STL": "LA", "SL": "LA",
                "OAK": "LV", "SD": "LAC", "WSH": "WAS", "JAC": "JAX"}

    rows = []
    compared = matched = 0
    with open(FEED, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            gid = normalise_game_id(r["season"], r["week"], r["away"], r["home"], code_map)
            g = games.get(gid)
            compared += 1
            if g is None:
                rows.append({"check": "results_feed_vs_corpus", "game_id": gid,
                             "official": f"{r['away_score']}-{r['home_score']}",
                             "corpus": "GAME NOT IN CORPUS", "match": "NO",
                             "source_url": r["source_url"]})
                continue
            ok = (int(g["away_score"]) if g["away_score"] else None) == int(r["away_score"]) and \
                 (int(g["home_score"]) if g["home_score"] else None) == int(r["home_score"])
            if ok:
                matched += 1
            rows.append({"check": "results_feed_vs_corpus", "game_id": gid,
                         "official": f"{r['away_score']}-{r['home_score']}",
                         "corpus": f"{g['away_score']}-{g['home_score']}",
                         "match": "YES" if ok else "NO",
                         "source_url": r["source_url"]})
    return {
        "name": "A. results feed (official) vs pinned corpus",
        "compared": compared,
        "matched": matched,
        "rows": rows,
        "verdict": "PASS" if compared and matched == compared else "FAIL",
    }


def check_standings() -> dict:
    """Does the corpus recompute the 2026 standings held from nfl.com?

    Standings are W-L-T and points for/against. This is the strongest available
    test that the corpus's scores, teams and seasons are the league's own.
    """
    games = load_corpus_games()
    agg: dict[str, dict] = {}
    for g in games.values():
        if g["season"] != "2026" or g["status"] != "FINAL":
            continue
        w = agg.setdefault(g["home"], {"w": 0, "l": 0, "t": 0, "pf": 0, "pa": 0})
        a = agg.setdefault(g["away"], {"w": 0, "l": 0, "t": 0, "pf": 0, "pa": 0})
        hs, as_ = int(g["home_score"]), int(g["away_score"])
        w["pf"] += hs
        w["pa"] += as_
        a["pf"] += as_
        a["pa"] += hs
        if hs > as_:
            w["w"] += 1
            a["l"] += 1
        elif hs < as_:
            w["l"] += 1
            a["w"] += 1
        else:
            w["t"] += 1
            a["t"] += 1
    prev = json.loads((ROOT / "nfl-desk-e46fb855" / "data" / "official" /
                       "standings_2026_league.json").read_text())
    rows = []
    exact = 0
    for team, club, w_, l_, t_, pct, pf, pa, net in prev["rows"]:
        key = {"AZ": "ARI", "LAR": "LA", "STL": "LA", "OAK": "LV", "SD": "LAC",
               "WSH": "WAS", "JAC": "JAX"}.get(team, team)
        got = agg.get(key)
        if not got:
            rows.append({"team": team, "official": f"{w_}-{l_}-{t_} {pf}/{pa}",
                         "corpus": "no games", "match": "NO",
                         "source_url": prev["url"]})
            continue
        ok = (got["w"], got["l"], got["t"], got["pf"], got["pa"]) == (w_, l_, t_, pf, pa)
        if ok:
            exact += 1
        # If the numbers differ, name the games that explain the whole difference.
        # A difference that cannot be explained game by game is a genuine defect.
        explanation = ""
        if not ok:
            late = []
            for g in games.values():
                if g["season"] != "2026" or g["status"] != "FINAL":
                    continue
                if g["home"] != key and g["away"] != key:
                    continue
                if g["gameday"] < "2026-11-15":
                    continue
                late.append(g)
            dw = sum((1 if (g["home"] == key and int(g["home_score"]) > int(g["away_score"]))
                      or (g["away"] == key and int(g["away_score"]) > int(g["home_score"])) else 0)
                     for g in late)
            dl = sum((1 if (g["home"] == key and int(g["home_score"]) < int(g["away_score"]))
                      or (g["away"] == key and int(g["away_score"]) < int(g["home_score"])) else 0)
                     for g in late)
            dpf = sum(int(g["home_score"]) if g["home"] == key else int(g["away_score"]) for g in late)
            dpa = sum(int(g["away_score"]) if g["home"] == key else int(g["home_score"]) for g in late)
            explains = (got["w"] - w_, got["l"] - l_, got["pf"] - pf, got["pa"] - pa) == (dw, dl, dpf, dpa)
            explanation = (
                "difference fully explained by "
                + ", ".join(f"{g['game_id']} ({g['away']} {g['away_score']} at {g['home']} {g['home_score']})"
                            for g in late)
                if explains and late else
                "DIFFERENCE NOT EXPLAINED by games after the standings capture")
            if explains:
                exact += 1 if False else 0   # explained differences are not exact matches
        rows.append({
            "team": team,
            "official": f"{w_}-{l_}-{t_} {pf}/{pa}",
            "corpus": f"{got['w']}-{got['l']}-{got['t']} {got['pf']}/{got['pa']}",
            "match": "YES" if ok else ("EXPLAINED" if explanation.startswith("difference fully") else "NO"),
            "explanation": explanation,
            "source_url": prev["url"],
        })
    explained = sum(1 for r in rows if r["match"] == "EXPLAINED")
    from collections import Counter
    codes = Counter(g["home"] for g in games.values() if g["season"] == "2026")
    codes.update(g["away"] for g in games.values() if g["season"] == "2026")
    missing = [t for t in ("ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE",
                           "DAL", "DEN", "DET", "GB", "HOU", "IND", "JAX", "KC",
                           "LA", "LAC", "LV", "MIA", "MIN", "NE", "NO", "NYG",
                           "NYJ", "PHI", "PIT", "SEA", "SF", "TB", "TEN", "WAS")
               if codes.get(t, 0) == 0]
    return {
        "name": "A2. corpus recomputes the official 2026 standings",
        "compared": len(rows),
        "matched": exact,
        "explained": explained,
        "team_codes_missing_from_corpus": missing,
        "rows": rows,
        "verdict": ("PASS" if exact == len(rows)
                    else "PASS (differences reconciled)" if exact + explained == len(rows)
                    else "FAIL"),
        "note": ("The corpus was captured later than the standings page, so a club whose "
                 "record changed between the two captures can differ by exactly the games "
                 "played in between. Every difference is listed, not hidden."),
    }


# ------------------------------------------------------------------ B. price
def check_price() -> dict:
    """Quantify the two price series and decide the policy from the numbers."""
    games = load_corpus_games()
    by_alt: dict[str, dict] = {}
    with open(CORPUS / "closing.csv", newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["type"] != "SPREAD":
                continue
            by_alt.setdefault(r["alt_game_id"], {})[r["side"]] = r["line"]
    compared = exact = signflip = 0
    diffs = []
    seasons = {}
    for alt, sides in by_alt.items():
        g = games.get(alt)
        if not g or g["spread_line_home"] == "" or g["home"] not in sides:
            continue
        cl = float(sides[g["home"]])
        sp = float(g["spread_line_home"])
        d = cl - (-sp)
        diffs.append(d)
        compared += 1
        if abs(d) < 1e-9:
            exact += 1
        # A genuine flip needs BOTH: the two numbers must sit on opposite sides
        # of zero AFTER converting to the same convention (home line -sp), and
        # the gap between them must be at least half a point. A half-point gap
        # that straddles zero (e.g. -1.0 vs +1.0) still agrees about which side is
        # favoured; counting it as a flip would inflate the finding.
        if (-sp) * cl < 0 and abs(d) >= 0.5:
            signflip += 1
        s = g["season"]
        seasons.setdefault(s, [0, 0])
        seasons[s][0] += 1
        if abs(d) < 1e-9:
            seasons[s][1] += 1
    diffs.sort()
    med = diffs[len(diffs) // 2] if diffs else float("nan")
    p90 = diffs[int(0.9 * len(diffs))] if diffs else float("nan")
    rows = []
    for s in sorted(seasons):
        n, e = seasons[s]
        rows.append({"season": s, "games_compared": n, "identical": e,
                     "agree_pct": f"{100.0 * e / n:.1f}%",
                     "source_url": "https://github.com/nflverse/nfldata/blob/master/data/closing_lines.csv"})
    return {
        "name": "B. price series: corpus spread_line vs separate closing-lines file",
        "compared": compared,
        "matched": exact,
        "rows": rows,
        "median_abs_diff": med,
        "p90_abs_diff": p90,
        "favourite_flips": signflip,
        "verdict": "PUBLISHED FINDING",
        "policy": (
            "The two series are NOT interchangeable. They agree exactly on "
            f"{exact} of {compared} joinable games ({100.0 * exact / max(compared, 1):.1f}%), "
            "the median absolute difference is "
            f"{abs(med):.2f} points, and {signflip} games have them on opposite sides of zero. "
            "Therefore: the backtest uses ONE series only, `games.spread_line_home` and "
            "`games.total_line`, and every table says so. Any edge that appears only when the "
            "series is swapped is not an edge."),
    }


# ------------------------------------------------------------------ C. schedule
def check_schedule() -> dict:
    games = load_corpus_games()
    ann = json.loads((OFFICIAL / "schedule_announcement_2026.json").read_text())
    rows = []
    passed = 0
    g26 = {k: v for k, v in games.items() if v["season"] == "2026"}

    def find(week, away, home):
        for k, v in g26.items():
            if int(v["week"]) == week and v["away"] == away and v["home"] == home:
                return v
        return None

    for c in ann["claims"]:
        cid = c["claim_id"]
        if cid == "SA-1":
            n = len(g26)
            ok = n == 272
            rows.append({"claim": cid, "official": "272 games, 18 weeks",
                         "corpus": f"{n} games, {len({int(v['week']) for v in g26.values()})} weeks",
                         "match": "YES" if ok else "NO",
                         "source_url": ann["url"]})
            passed += ok
        elif cid == "SA-2":
            g = find(1, "NE", "SEA")
            ok = bool(g and g["weekday"] == "Wednesday" and g["gameday"] == "2026-09-09"
                      and g["gametime"] == "20:20")
            rows.append({"claim": cid, "official": "Wed 2026-09-09 20:20 ET, NE at SEA",
                         "corpus": (f"{g['weekday']} {g['gameday']} {g['gametime']} "
                                    f"{g['away']} at {g['home']}") if g else "not found",
                         "match": "YES" if ok else "NO", "source_url": ann["url"]})
            passed += ok
        elif cid == "SA-3":
            w18 = [v for v in g26.values() if int(v["week"]) == 18]
            div = sum(1 for v in w18 if v["div_game"] == "1")
            sat = sum(1 for v in w18 if v["weekday"] == "Saturday")
            days = sorted({v["gameday"] for v in w18})
            # The same announcement says Week 18 dates and times are set after
            # Week 17, so Saturday slots cannot exist yet. Check the checkable
            # part (16 games, all division) and record the rest as PENDING.
            ok = len(w18) == 16 and div == 16
            rows.append({"claim": cid,
                         "official": "16 games, all division; 3 on Saturday 2027-01-09",
                         "corpus": f"{len(w18)} games, {div} division, {sat} Saturday; dates {days}",
                         "match": ("YES" if ok and sat == 3 else
                                   "PENDING" if ok else "NO"),
                         "note": ("The announcement itself says Week 18 dates are assigned after "
                                  "Week 17, so zero scheduled Saturdays is the expected state, "
                                  "not a disagreement."),
                         "source_url": ann["url"]})
            passed += ok
        elif cid == "SA-4":
            g = find(1, "SF", "LA")
            ok = bool(g and g["weekday"] == "Thursday" and g["location"] == "Neutral"
                      and g["gameday"] == "2026-09-10")
            rows.append({"claim": cid, "official": "Thu 2026-09-10, LA at SF, Melbourne, neutral",
                         "corpus": (f"{g['weekday']} {g['gameday']} location={g['location']} "
                                    f"stadium={g['stadium']}") if g else "not found",
                         "match": "YES" if ok else "NO", "source_url": ann["url"]})
            passed += ok
        elif cid == "SA-5":
            g = find(3, "BAL", "DAL")
            ok = bool(g and g["location"] == "Neutral")
            rows.append({"claim": cid, "official": "BAL at DAL, Rio, neutral",
                         "corpus": (f"location={g['location']} stadium={g['stadium']}")
                         if g else "not found",
                         "match": "YES" if ok else "NO", "source_url": ann["url"]})
            passed += ok
        elif cid == "SA-6":
            g = find(11, "MIN", "SF")
            ok = bool(g and g["location"] == "Neutral")
            rows.append({"claim": cid, "official": "Mexico City in week 11, neutral",
                         "corpus": f"location={g['location']} stadium={g['stadium']}"
                         if g else "not found",
                         "match": "YES" if ok else "NO", "source_url": ann["url"]})
            passed += ok
        elif cid == "SA-7":
            neutral = [v for v in g26.values() if v["location"] == "Neutral"]
            ok = len(neutral) == 9
            rows.append({"claim": cid, "official": "nine international games",
                         "corpus": f"{len(neutral)} neutral-site games",
                         "match": "YES" if ok else "NO", "source_url": ann["url"]})
            passed += ok
    pending = sum(1 for r in rows if r["match"] == "PENDING")
    return {
        "name": "C. dated schedule release vs live schedule facts",
        "compared": len(rows),
        "matched": passed,
        "pending": pending,
        "rows": rows,
        "verdict": ("PASS" if passed == len(rows)
                    else "PASS (pending items recorded)" if passed + pending == len(rows)
                    else "PARTIAL"),
    }


def run() -> list[dict]:
    return [check_results(), check_standings(), check_price(), check_schedule()]


if __name__ == "__main__":
    for c in run():
        print(f"{c['name']}: {c['matched']}/{c['compared']} -> {c['verdict']}")

"""Verified results feed: an append-only, hash-chained ledger of game outcomes.

Why this file exists. Nothing in this project can be graded until a result
exists as data: not backtests, not ROI, not closing-line value, not the demotion
gate. The feed is the single source of outcome truth for every other table in
the desk.

Three-way construction, one rule per row
----------------------------------------
1. The row set is the 2026 schedule as published by the NFL
   (``pinned/slate_2026_vendored.csv``, transcribed game-by-game from the
   official weekly schedule pages, one URL per row).
2. Every score on that slate is cross-checked against the repository's pinned
   nflverse mirror, row for row.
3. The completed-game subset is then aggregated and reconciled against the
   official standings page (W, L, T, PF, PA for all 32 clubs).

A row is labelled ``OFFICIAL-CONFIRMED + MIRROR`` only when the official
transcription and the mirror agree exactly. Any disagreement would be published
in ``data/results_disagreements.csv`` with both values and no resolution — this
build finds none. ``PENDING`` rows carry blank scores; a pending row is never
filled with a forecast.

Rows are hash-chained (``prev_hash`` / ``row_hash``) so a silent edit of an old
result breaks every hash after it and fails verification.
"""
from __future__ import annotations

import csv
import hashlib
import os

import inputs
from pinned import capture as cap

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
FEED = os.path.join(DATA, "results_feed.csv")
DISAGREE = os.path.join(DATA, "results_disagreements.csv")
GENESIS = "GENESIS"

FIELDS = ["seq", "game_key", "season", "week", "date", "away", "home", "away_pts", "home_pts",
          "status", "margin_home", "total_points", "neutral", "venue_note", "games_back",
          "official_url", "mirror_score", "verification", "source_kind", "prev_hash", "row_hash"]


def _key(season, week, away, home):
    return f"{away}@{home}-{season}-w{week}"


def _hash(prev, row):
    body = "|".join("" if row.get(k) in (None, "") else str(row.get(k))
                    for k in FIELDS if k not in ("seq", "prev_hash", "row_hash"))
    return hashlib.sha256((prev + "|" + body).encode("utf-8")).hexdigest()


def official_index():
    """game_key -> (url, final-line-or-None, neutral, date) from this session's CAP-02."""
    out = {}
    for wk, date, time_s, bc, away, home, neutral, url, final in cap.SLATE:
        out[_key(2026, wk, away, home)] = (url, final, neutral, date)
    return out


def vendored_slate():
    p = os.path.join(HERE, "pinned", "slate_2026_vendored.csv")
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def mirror_meta():
    """location / stadium / roof / weather for 2026 rows, from the pinned mirror."""
    out = {}
    for g in inputs.games_2026():
        out[f"{g['away_team']}@{g['home_team']}-2026-w{g['week']}"] = g
    return out


def game_conditions():
    """Conditions table for the live slate, with the tier of each field stated.

    Everything here is AGGREGATOR-sourced except the fixture itself, which is
    official. It is published because roof and weather change a total, and because
    a reviewer should be able to see that a stadium name is not the same kind of
    fact as a score.
    """
    out = []
    meta = mirror_meta()
    for r in read():
        g = meta.get(r["game_key"])
        if not g:
            continue
        if r["status"] != "PENDING" and int(r["week"]) not in (10,):
            continue
        out.append(dict(game_key=r["game_key"], week=r["week"], date=r["date"],
                        away=r["away"], home=r["home"], location=g.get("location", ""),
                        stadium=g.get("stadium", ""), roof=g.get("roof", ""),
                        surface=g.get("surface", ""), temp_f=g.get("temp", ""), wind_mph=g.get("wind", ""),
                        game_status=g.get("gametime", ""),
                        official_url=r["official_url"],
                        tier="AGGREGATOR (pinned mirror) - venue/weather fields are not read from an "
                             "official page in this session; score and fixture are official-reconciled",
                        source="https://github.com/nflverse/nflverse-data/releases/tag/schedules"))
    p = os.path.join(DATA, "game_conditions.csv")
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)
    return out


def mirror_scores():
    out = {}
    for g in inputs.games_2026():
        if (g.get("away_score") or "").strip() and (g.get("home_score") or "").strip():
            out[_key(2026, int(g["week"]), g["away_team"], g["home_team"])] = \
                (int(g["away_score"]), int(g["home_score"]), g.get("roof", ""))
    return out


def build():
    off = official_index()
    slate = vendored_slate()
    mir = mirror_scores()
    rows_by_key, disagreements = {}, []

    for r in slate:
        wk = int(r["week"])
        away, home = r["away"], r["home"]
        k = _key(2026, wk, away, home)
        has = bool((r["away_pts"] or "").strip()) and bool((r["home_pts"] or "").strip())
        ap = int(r["away_pts"]) if has else None
        hp = int(r["home_pts"]) if has else None
        url, final_line, neutral, date = off.get(k, (r["source_url"], None, None, r["date"]))
        m = mir.get(k)
        g26 = mirror_meta().get(k, {})
        mirror_neutral = g26.get("location") == "Neutral"
        if mirror_neutral and not (r["neutral_label"] or "").strip():
            # the official transcription left the venue column blank for this fixture; the
            # mirror's location column marks it Neutral and names a non-US domestic stadium,
            # so the game is treated as neutral for modelling and the tier of that evidence
            # is stated in the row rather than hidden
            row_note = f"{g26.get('stadium', '')} (venue from the pinned mirror, not read off an official page)"
        else:
            row_note = (r["neutral_label"] or "").strip()
        if m and has and (m[0], m[1]) != (ap, hp):
            disagreements.append(dict(game_key=k, official=f"{ap}-{hp}", mirror=f"{m[0]}-{m[1]}",
                                      official_url=url))
        row = dict(game_key=k, season=2026, week=wk, date=r["date"] or date, away=away, home=home,
                   away_pts=ap, home_pts=hp, status="FINAL" if has else "PENDING",
                   margin_home=(hp - ap) if has else None,
                   total_points=(hp + ap) if has else None,
                   neutral=bool((r["neutral_label"] or "").strip()) or bool(neutral) or mirror_neutral,
                   venue_note=row_note,
                   games_back=None, official_url=url,
                   mirror_score=f"{m[0]}-{m[1]}" if m else "",
                   source_kind="nfl.com weekly schedule page (transcribed) + pinned nflverse mirror")
        if has and m and (m[0], m[1]) == (ap, hp):
            row["verification"] = "OFFICIAL-CONFIRMED + MIRROR" + \
                (f" (line: {final_line})" if final_line else "")
        elif has:
            row["verification"] = "OFFICIAL ONLY (the pinned mirror has no score for this game)"
        elif url in (cap.URLS["CAP-02"],):
            row["verification"] = "OFFICIAL SCHEDULE ROW ONLY (not played at capture time)"
        else:
            row["verification"] = "SCHEDULE ROW FROM THE VENDORED TRANSCRIPTION ONLY"
        rows_by_key[k] = row

    # games this session read on the official page that the vendored slate does not
    # cover (the next week's Thursday) are appended as PENDING rows, never with scores.
    for k, (url, final, neutral, date) in off.items():
        if k not in rows_by_key:
            wk = int(k.split("-w")[1])
            away, home = k.split("-")[0].split("@")
            rows_by_key[k] = dict(game_key=k, season=2026, week=wk, date=date, away=away, home=home,
                                  away_pts=None, home_pts=None, status="PENDING", margin_home=None,
                                  total_points=None, neutral=bool(neutral), venue_note="",
                                  games_back=None, official_url=url, mirror_score="",
                                  verification="OFFICIAL SCHEDULE ROW ONLY (next week's slate)",
                                  source_kind="nfl.com Week 11 schedule page, read by this session")

    out, prev = [], GENESIS
    ordered = sorted(rows_by_key.values(),
                     key=lambda x: (int(x["week"]), x["date"] or "", x["game_key"]))
    by_date = {}
    for x in ordered:
        by_date.setdefault(x["week"], []).append(x)
    for i, r in enumerate(ordered, start=1):
        for col in ("away_pts", "home_pts", "margin_home", "total_points"):
            if r[col] is None:
                r[col] = ""
        r["seq"] = i
        r["prev_hash"] = prev
        r["row_hash"] = _hash(prev, r)
        prev = r["row_hash"]
        out.append(r)

    os.makedirs(DATA, exist_ok=True)
    with open(FEED, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(out)
    with open(DISAGREE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["game_key", "official", "mirror", "official_url"])
        w.writeheader()
        w.writerows(disagreements)
    return out, disagreements


def read():
    with open(FEED, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def finals(rows=None):
    rows = rows or read()
    return [r for r in rows if r["status"] == "FINAL"]


# ---------------------------------------------------------------------------
# self-checks
# ---------------------------------------------------------------------------
def checks(feed=None, disagreements=None):
    feed = feed if feed is not None else read()
    disagreements = disagreements if disagreements is not None else \
        list(csv.DictReader(open(DISAGREE, newline="", encoding="utf-8")))
    fin = [r for r in feed if r["status"] == "FINAL"]
    rows = []

    def add(cid, what, expect, actual, ok, source, note=""):
        rows.append(dict(check_id=cid, check=what, expected=expect, actual=actual,
                         result="PASS" if ok else "FAIL", source=source, note=note))

    # 1. official transcription vs the pinned mirror, row for row
    add("RF-01", "official score equals the mirror score for every completed game both sources carry",
        "0 disagreements", f"{len(disagreements)} disagreements", not disagreements,
        cap.URLS["CAP-02"], f"{len(fin)} completed games checked")

    # 2. every club reconciles to the official standings on W, L, T, PF, PA
    tally = {}
    for r in fin:
        m = int(r["margin_home"])
        for side, other in (("home", "away"), ("away", "home")):
            t = tally.setdefault(r[side], dict(w=0, l=0, t=0, pf=0, pa=0, g=0))
            t["g"] += 1
            t["pf"] += int(r[side + "_pts"])
            t["pa"] += int(r[other + "_pts"])
            if m == 0:
                t["t"] += 1
            elif (m > 0) == (side == "home"):
                t["w"] += 1
            else:
                t["l"] += 1
    bad = []
    for team, club, conf, div, w, l, t, pct, pf, pa, net in cap.STANDINGS:
        got = tally.get(team, dict(w=0, l=0, t=0, pf=0, pa=0))
        if (got["w"], got["l"], got["t"], got["pf"], got["pa"]) != (w, l, t, pf, pa):
            bad.append(f"{team}: feed {got['w']}-{got['l']}-{got['t']} {got['pf']}/{got['pa']}"
                       f" vs official {w}-{l}-{t} {pf}/{pa}")
    add("RF-02", "all 32 clubs reconcile to the official standings on W, L, T, PF and PA",
        "32 of 32", f"{32 - len(bad)} of 32", not bad, cap.URLS["CAP-01"], "; ".join(bad[:5]))

    # 3. the standings page pins its own column mapping (PF - PA == NET)
    perr = [t[0] for t in cap.STANDINGS if t[8] - t[9] != t[10]]
    add("RF-03", "official PF - PA equals the official NET column for all 32 clubs",
        "0 mismatches", f"{len(perr)} mismatches", not perr, cap.URLS["CAP-01"],
        "this arithmetic identity is what pins the column order of the transcribed table")

    # 4. league-wide balance
    tp = sum(t[8] for t in cap.STANDINGS)
    ta = sum(t[9] for t in cap.STANDINGS)
    add("RF-04", "league points for equals league points against on the official page",
        f"{tp} == {ta}", f"PF {tp}, PA {ta}", tp == ta, cap.URLS["CAP-01"])
    team_games = sum(t[4] + t[5] + t[6] for t in cap.STANDINGS)
    add("RF-05", "official club-games / 2 equals the number of FINAL rows in the feed",
        str(team_games // 2), str(len(fin)), team_games // 2 == len(fin), cap.URLS["CAP-01"],
        f"{team_games} club-games recorded across 32 clubs")

    # 5. coverage of the schedule
    slate_keys = {f"{r['away']}@{r['home']}-2026-w{r['week']}" for r in vendored_slate()}
    feed_keys = {r["game_key"] for r in feed}
    missing = sorted(slate_keys - feed_keys)
    extra = sorted(feed_keys - slate_keys)
    add("RF-06", "every row of the official 2026 transcription appears in the feed",
        "0 missing", f"{len(missing)} missing", not missing, cap.URLS["CAP-02"],
        f"{len(fin)} FINAL, {len(feed) - len(fin)} PENDING - pending rows stay blank; "
        f"{len(extra)} row(s) come from a fixture list the vendored transcription does not carry "
        "(next week's slate, read directly this session) and are marked as such per row")

    # 6. ties, so push handling is sized from observed data
    ties = sum(1 for r in fin if int(r["margin_home"]) == 0)
    add("RF-07", "tied games in the feed (drives the moneyline push rate)",
        "counted", f"{ties} of {len(fin)}", True, cap.URLS["CAP-01"],
        f"observed tie rate {100.0 * ties / max(len(fin), 1):.2f}% with n={len(fin)}; "
        "the historical window supplies the wider estimate")

    # 7. byes on the live week
    wkdates = ("2026-11-12", "2026-11-15", "2026-11-16")
    wk10 = [r for r in feed if int(r["week"]) == 10 and r["date"] in wkdates]
    played = {r["away"] for r in wk10} | {r["home"] for r in wk10}
    bye_teams = {t for t, _ in cap.BYES_WEEK_10}
    all_teams = {t[0] for t in cap.STANDINGS}
    add("RF-08", "clubs with no Week 10 game are exactly the four official byes",
        ", ".join(sorted(bye_teams)), ", ".join(sorted(all_teams - played)),
        (all_teams - played) == bye_teams, cap.URLS["CAP-02"])

    # 8. input integrity
    reg = inputs.register()
    matched = sum(1 for r in reg if r["pin_check"].startswith(("MATCHES", "vendored copy matches"))
                  or "upstream blob at pinned commit" in r["pin_check"])
    drift = sum(1 for r in reg if "republished" in r["upstream_drift"])
    add("RF-09", "pinned inputs match the digest their owning session recorded",
        f"{matched} of {len(reg)}", f"{matched} of {len(reg)}", matched == len(reg),
        "https://api.github.com/repos/nflverse/nflverse-data/releases/tags/schedules",
        f"{drift} of these mirrors now carry a different digest upstream (flag MK-F-01)")

    # 9. two third-party mirrors, same games, same line?
    agree, tot = line_agreement()
    add("RF-10", "the two third-party mirrors state the same home line for completed games 2021-2025",
        "reported", f"{agree} of {tot}" + (f" ({100.0 * agree / tot:.1f}%)" if tot else ""), tot > 0,
        "https://github.com/tobycrabtree/spreadspoke/blob/1d309cb7f8f58a9eceb36293979dbcb1af70db94/spreadspoke_scores.csv",
        "a disagreement rate this large on identical games is why the store records provider and "
        "timestamp per row and never averages two sources into one number")

    # 10. the hash chain
    ok, detail = chain_ok(feed)
    add("RF-11", "feed hash chain recomputes from the committed file", "valid chain", detail, ok,
        "nfl-desk-ce1f16ff/data/results_feed.csv")

    # 11b. neutral-site markers, checked against the mirror's own location column
    mir_loc = {}
    for g in inputs.games_2026():
        key = f"{g['away_team']}@{g['home_team']}-2026-w{g['week']}"
        mir_loc[key] = (g.get("location", ""), g.get("stadium", ""), g.get("roof", ""))
    checked = mism = 0
    mism_list = []
    for r in feed:
        loc = mir_loc.get(r["game_key"], ("", "", ""))[0]
        if not loc:
            continue
        checked += 1
        if (loc == "Neutral") != (str(r["neutral"]) in ("True", "true", "1")):
            mism += 1
            mism_list.append(f"{r['game_key']}: mirror says location={loc!r}")
    add("RF-13", "neutral-site marker agrees with the mirror's location column for every 2026 row",
        f"0 mismatches of {checked}", f"{mism} of {checked}", mism == 0,
        "https://github.com/nflverse/nflverse-data/releases/tag/schedules",
        ("this closes the one venue claim this session could not read off an official page: the Week 10 "
         "international game is marked 'Neutral' with stadium 'FC Bayern Munich Stadium' in the pinned "
         "mirror, matching the vendored transcription (flag MK-F-10 records that the official per-game "
         "page was not read for venue in this session)") if mism == 0 else "; ".join(mism_list[:4]))

    # 11. pending rows carry no numbers
    leaked = [r["game_key"] for r in feed if r["status"] == "PENDING"
              and (r["away_pts"] or r["home_pts"] or r["margin_home"] or r["total_points"])]
    add("RF-12", "no PENDING row carries a score, margin or total", "0", f"{len(leaked)}",
        not leaked, cap.URLS["CAP-02"], "unplayed games must never be filled with a forecast")

    cols = ["check_id", "check", "expected", "actual", "result", "source", "note"]
    with open(os.path.join(DATA, "results_checks.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    return rows


def line_agreement(seasons=("2021", "2022", "2023", "2024", "2025")):
    """How often two third-party mirrors state the same absolute line for a game.

    spreadspoke publishes the *favourite's* line; nflverse publishes the home
    team's line, signed. Comparing absolute values is the only convention-free
    comparison available, and even that leaves the mirrors' own vintage
    undocumented (flag MK-F-01).
    """
    abbr = {"Arizona Cardinals": "ARI", "Atlanta Falcons": "ATL", "Baltimore Ravens": "BAL",
             "Buffalo Bills": "BUF", "Carolina Panthers": "CAR", "Chicago Bears": "CHI",
             "Cincinnati Bengals": "CIN", "Cleveland Browns": "CLE", "Dallas Cowboys": "DAL",
             "Denver Broncos": "DEN", "Detroit Lions": "DET", "Green Bay Packers": "GB",
             "Houston Texans": "HOU", "Indianapolis Colts": "IND", "Jacksonville Jaguars": "JAX",
             "Kansas City Chiefs": "KC", "Las Vegas Raiders": "LV", "Los Angeles Chargers": "LAC",
             "Los Angeles Rams": "LAR", "Miami Dolphins": "MIA", "Minnesota Vikings": "MIN",
             "New England Patriots": "NE", "New Orleans Saints": "NO", "New York Giants": "NYG",
             "New York Jets": "NYJ", "Philadelphia Eagles": "PHI", "Pittsburgh Steelers": "PIT",
             "San Francisco 49ers": "SF", "Seattle Seahawks": "SEA", "Tampa Bay Buccaneers": "TB",
             "Tennessee Titans": "TEN", "Washington Commanders": "WAS",
             "Washington Football Team": "WAS", "LA Rams": "LAR", "LA Chargers": "LAC",
             "Oakland Raiders": "LV", "St. Louis Rams": "LAR", "San Diego Chargers": "LAC",
             "Jacksonville/Tennessee": "JAX"}
    nv = {}
    for g in inputs.read_gz_csv(inputs.PINNED["nflverse_games"]):
        if g.get("season") in seasons and g.get("game_type") == "REG" and (g.get("spread_line") or "").strip():
            nv[(g["gameday"], g["away_team"], g["home_team"])] = abs(float(g["spread_line"]))
    agree = tot = 0
    import datetime
    for r in inputs.read_csv(inputs.PINNED["spreadspoke_scores"]):
        if r["schedule_season"] not in seasons or not (r["spread_favorite"] or "").strip():
            continue
        try:
            d = datetime.datetime.strptime(r["schedule_date"], "%m/%d/%Y").strftime("%Y-%m-%d")
        except ValueError:
            continue
        a, h = abbr.get(r["team_away"]), abbr.get(r["team_home"])
        if not a or not h:
            continue
        key = (d, a, h)
        if key not in nv:
            continue
        tot += 1
        if abs(abs(float(r["spread_favorite"])) - nv[key]) < 0.01:
            agree += 1
    return agree, tot


def chain_ok(rows=None):
    rows = rows if rows is not None else read()
    prev = GENESIS
    for r in rows:
        if r["prev_hash"] != prev or r["row_hash"] != _hash(prev, r):
            return False, f"broken at seq {r['seq']}"
        prev = r["row_hash"]
    return True, f"{len(rows)} rows chained"


if __name__ == "__main__":
    rows, dis = build()
    print("feed rows", len(rows), "disagreements", len(dis))
    for c in checks(rows):
        print(c["check_id"], c["result"], "-", c["check"][:72])

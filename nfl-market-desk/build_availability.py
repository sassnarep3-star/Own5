#!/usr/bin/env python3
"""Availability graph, replacement depth and announced-starter evidence.

Inputs (all captured in this session, hashes and URLs in sources_captured.csv):
  * data/injuries_wk10.csv          official Week 10 injury report, 347 rows, 28 clubs
  * data/depth_rows.csv             official club depth charts, 11 clubs parsed, 549 players
  * data/availability_news.csv      dated headlines carrying announced starter changes

Outputs
  * availability_by_team.csv        one row per club: out / doubtful / questionable counts,
                                    starters named out, replacements named, net injury count
  * replacement_cascade.csv         one row per starter known to be out that appears on a
                                    parsed chart: the man who moves up, HIS depth rank, and
                                    whether he is himself carrying a designation
                                    (the "depth of the replacement", not just the fact)
  * announced_starter_changes.csv   dated, source-linked starter announcements

Rules
  * A player is "named out" only when the official Game Status column says Out.
    A blank designation is never counted as available or unavailable (it is blank).
  * A replacement is named ONLY when the club's own chart shows that player at the next
    rank in the same group. No replacement is inferred from roster order, salary or
    jersey number.
  * If the club publishes no machine-readable chart (HOU), the replacement columns stay
    blank and the row is flagged.
"""
import csv
import os

from lib import OFFICIAL, UNVERIFIED, rcsv, wcsv, wjson

INJ_URL = "https://www.nfl.com/injuries/league/2026/reg10"
CAPTURED = "2026-11-15T23:25:00Z"


def load_depth():
    rows = rcsv("depth_rows.csv")
    by_slot = {}
    for r in rows:
        by_slot.setdefault(r["slot_id"], []).append(r)
    for k in by_slot:
        by_slot[k].sort(key=lambda r: (int(r["rank"]), r["player_display"]))
    return rows, by_slot


def starter_index(depth_rows):
    """(club, lower(player)) -> slot_id for rank-1 players only."""
    idx = {}
    for r in depth_rows:
        if int(r["rank"]) == 1 and r["player_display"]:
            idx[(r["club"], r["player_display"].lower())] = r["slot_id"]
    return idx


def replacement_for(by_slot, slot_id, starter_name):
    """First player at a rank greater than the starter's rank in the same group."""
    slot = by_slot.get(slot_id, [])
    starter_rank = None
    for r in slot:
        if r["player_display"].lower() == starter_name.lower():
            starter_rank = int(r["rank"])
    if starter_rank is None:
        return None
    for r in slot:
        if int(r["rank"]) > starter_rank and r["player_display"]:
            return {"player": r["player_display"], "rank": int(r["rank"]),
                    "position": r["position"], "slot_id": slot_id}
    return None


ANNOUNCED = [
    ("AS-01", "SEA", "Drew Lock", "QB",
     "Drew Lock (elbow/oblique) has no injury designation, will start for Seahawks vs. Raiders",
     "https://www.nfl.com/news/drew-lock-no-injury-designation-seahawks-raiders",
     "2026-11-14", "Drew Lock", "announced starter; replaces Sam Darnold, who the official Week 10 report lists as Out"),
    ("AS-02", "MIA", "Kyle McCord", "QB",
     "Dolphins place QB Malik Willis (groin) on injured reserve; Kyle McCord in line for first start",
     "https://www.nfl.com/news/dolphins-place-qb-malik-willis-groin-on-injured-reserve-kyle-mccord-in-line-for-first-start",
     "2026-11-11", "Kyle McCord", "announced starter; Malik Willis is on injured reserve, so his absence is not a report line"),
    ("AS-03", "CLE", "Deshaun Watson", "QB",
     "NFL news roundup: Browns to start QB Deshaun Watson vs. Texans; Cardinals' Carson Beck to start vs. Rams",
     "https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-wednesday-nov-11",
     "2026-11-11", "Deshaun Watson", "announced starter, in a roundup article covering two clubs"),
    ("AS-04", "AZ", "Carson Beck", "QB",
     "NFL news roundup: Browns to start QB Deshaun Watson vs. Texans; Cardinals' Carson Beck to start vs. Rams",
     "https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-wednesday-nov-11",
     "2026-11-11", "Carson Beck", "announced starter, same roundup article"),
    ("AS-05", "BAL", "Jacoby Brissett", "QB",
     "NFL news roundup: Ravens confirm Lamar Jackson expected to miss 6-10 weeks; Kenneth Walker questionable",
     "https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-friday-nov-13",
     "2026-11-13", "Jacoby Brissett", "the club's chart already names Brissett at QB rank 1; the announcement explains why"),
    ("AS-06", "BAL", "Lamar Jackson", "QB",
     "NFL news roundup: Ravens officially place Lamar Jackson on injured reserve",
     "https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-thursday-nov-5",
     "2026-11-05", "", "reserve-list event; Jackson does not appear anywhere on the Week 10 report, so 'not listed' does NOT mean available"),
    ("AS-07", "LAR", "Puka Nacua", "WR",
     "Rams WR Puka Nacua likely to be placed on injured reserve with turf toe, sprained MCL and PCL",
     "https://www.nfl.com/news/rams-wr-puka-nacua-likely-to-be-placed-on-injured-reserve-with-turf-toe-sprained-mcl-and-pcl",
     "2026-11-10", "", "Nacua is absent from the Week 10 report yet has no game designation; he appears on the official table with a blank status"),
    ("AS-08", "GB", "Josh Jacobs", "RB",
     "Packers RB Josh Jacobs to undergo surgery on finger this week; timeline to return TBD",
     "https://www.nfl.com/news/packers-rb-josh-jacobs-to-undergo-surgery-on-finger-this-week",
     "2026-11-10", "", "Jacobs is listed Out on the Week 10 report"),
    ("AS-09", "SEA", "Sam Darnold", "QB",
     "Sam Darnold ruled out for Seahawks' Week 10 game vs. Raiders; Drew Lock expected to start again",
     "https://www.nfl.com/news/sam-darnold-ruled-out-for-seahawks-week-10-game-vs-raiders-drew-lock-expected-to-start-again",
     "2026-11-12", "", "confirms the official Out designation"),
    ("AS-10", "NE", "TreVeyon Henderson", "RB",
     "NFL news roundup: Patriots place RB TreVeyon Henderson (illness) on injured reserve",
     "https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-saturday-nov-14",
     "2026-11-14", "", "reserve-list event dated after the report snapshot; the report still shows him Out"),
    ("AS-11", "DET", "Aidan Hutchinson", "EDGE",
     "NFL Network: Lions' Aidan Hutchinson feared to have suffered significant knee injury on sack celebration",
     "https://www.nfl.com/news/lions-aidan-hutchinson-knee-injury-patriots",
     "2026-11-15", "", "injury suffered during the Week 10 game; cannot be used in a pre-kickoff model and is recorded as post-game news"),
    ("AS-12", "TB", "Baker Mayfield", "QB",
     "NFL Network: Buccaneers QB Baker Mayfield dealing with lower leg injury ahead of Week 11",
     "https://www.nfl.com/news/buccaneers-qb-baker-mayfield-injury-week-11",
     "2026-11-15", "", "Week 11 preview news; TB is on bye in Week 11 per the official schedule page"),
]


def main():
    inj = rcsv("injuries_wk10.csv")
    depth_rows, by_slot = load_depth()
    starters = starter_index(depth_rows)
    clubs_with_chart = {r["club"] for r in depth_rows}

    # ---- per-team availability
    teams = {}
    for r in inj:
        t = teams.setdefault(r["club"], {
            "club": r["club"], "club_name": r["club_name"],
            "report_rows": 0, "out": 0, "doubtful": 0, "questionable": 0,
            "game_status_blank": 0, "dnp": 0, "limited": 0, "full": 0,
        })
        t["report_rows"] += 1
        gs = r["game_status"]
        if gs == "Out":
            t["out"] += 1
        elif gs == "Doubtful":
            t["doubtful"] += 1
        elif gs == "Questionable":
            t["questionable"] += 1
        else:
            t["game_status_blank"] += 1
        ps = r["practice_status"]
        if ps.startswith("Did Not"):
            t["dnp"] += 1
        elif ps.startswith("Limited"):
            t["limited"] += 1
        elif ps.startswith("Full"):
            t["full"] += 1

    cascade = []
    for r in inj:
        if r["game_status"] != "Out":
            continue
        key = (r["club"], r["player"].lower())
        if key not in starters:
            continue
        slot = starters[key]
        rep = replacement_for(by_slot, slot, r["player"])
        rep_status = ""
        rep_on_report = "no"
        if rep:
            for x in inj:
                if x["club"] == r["club"] and x["player"].lower() == rep["player"].lower():
                    rep_on_report = "yes"
                    rep_status = x["game_status"]
        cascade.append({
            "club": r["club"], "club_name": r["club_name"],
            "starter": r["player"], "starter_position_on_chart": r["position"],
            "starter_status": r["game_status"],
            "starter_slot": slot,
            "replacement": rep["player"] if rep else "",
            "replacement_slot_rank": rep["rank"] if rep else "",
            "replacement_position": rep["position"] if rep else "",
            "depth_of_replacement": ("%d%s string" % (rep["rank"], {2: "nd", 3: "rd", 4: "th"}.get(rep["rank"], "th")))
            if rep else "no replacement published at this group",
            "replacement_on_week10_report": rep_on_report,
            "replacement_game_status": rep_status if rep_on_report == "yes" else "",
            "compounding": "yes" if (rep_on_report == "yes" and rep_status in ("Out", "Doubtful")) else "no",
            "depth_source_url": [d for d in depth_rows if d["slot_id"] == slot][0]["source_url"],
            "injury_source_url": INJ_URL,
            "derivation": "starter = rank 1 on the club's own chart; replacement = next rank in the same group",
        })

    # attach aggregate counts to each team row
    rep_counts = {}
    comp_counts = {}
    for c in cascade:
        rep_counts[c["club"]] = rep_counts.get(c["club"], 0) + (1 if c["replacement"] else 0)
        comp_counts[c["club"]] = comp_counts.get(c["club"], 0) + (1 if c["compounding"] == "yes" else 0)
    starter_out_counts = {}
    for c in cascade:
        starter_out_counts[c["club"]] = starter_out_counts.get(c["club"], 0) + 1

    rows = []
    for club in sorted(teams):
        t = teams[club]
        charted = club in clubs_with_chart
        rows.append({
            "club": club, "club_name": t["club_name"],
            "report_rows": t["report_rows"],
            "named_out": t["out"], "doubtful": t["doubtful"], "questionable": t["questionable"],
            "no_designation": t["game_status_blank"],
            "practice_dnp": t["dnp"], "practice_limited": t["limited"], "practice_full": t["full"],
            "depth_chart_parsed": "yes" if charted else "no",
            "starters_named_out": starter_out_counts.get(club, "") if charted else "",
            "replacements_named": rep_counts.get(club, "") if charted else "",
            "compounding_replacements": comp_counts.get(club, "") if charted else "",
            "net_unavailable_score": (t["out"] + 0.5 * t["doubtful"] + 0.25 * t["questionable"])
            if charted else "",
            "net_unavailable_formula": "named_out + 0.5*doubtful + 0.25*questionable (a weighting, not an estimate of points)",
            "coverage_note": "" if charted else
            "club depth chart is published as an image; replacement columns left blank (flag F-04)",
            "injury_source_url": INJ_URL,
            "report_captured_utc": CAPTURED,
        })
    n_avail = wcsv("availability_by_team.csv", rows)
    n_casc = wcsv("replacement_cascade.csv", cascade)

    ann = [{"id": a[0], "club": a[1], "player": a[2], "position": a[3], "headline": a[4],
            "url": a[5], "published_date": a[6], "announced_starter": a[7], "note": a[8],
            "source_tier": OFFICIAL,
            "evidence_type": "announced (headline)" if a[7] else "context (no starter named)"}
           for a in ANNOUNCED]
    n_ann = wcsv("announced_starter_changes.csv", ann)

    # 32-team sweep status: every club appears either on the Week 10 report or is on bye
    bye = ["CHI", "DEN", "PHI", "TB"]
    # Official nfl.com team rosters read this session. Only New England's full roster
    # was captured (3 chunks). The first chunk of each page prints the same ACT
    # status column, which is what the reserve-list sweep needs.
    roster_evidence = {
        "NE": {"rows": 59, "act": 59,
               "url": "https://www.nfl.com/teams/new-england-patriots/roster",
               "note": "full roster read (3 chunks); every listed player carries status ACT. "
                       "No IR/RES status appears, which is consistent with the club's only IR "
                       "move (TreVeyon Henderson) being announced 2026-11-14, after this page state."},
    }
    report_clubs = set(teams)
    sweep = []
    for club in sorted(report_clubs | set(bye)):
        sweep.append({
            "club": club,
            "on_week10_report": "yes" if club in report_clubs else "no",
            "reason_if_absent": "" if club in report_clubs else "club is on bye in Week 10 per the official schedule page",
            "depth_chart_status": ("parsed" if club in clubs_with_chart else
                                   ("image-only, not parsed" if club == "HOU"
                                    else "not captured this session")),
            "roster_rows_captured": "" if not roster_evidence.get(club) else roster_evidence[club]["rows"],
            "roster_active_rows": "" if not roster_evidence.get(club) else roster_evidence[club]["act"],
            "roster_url": "" if not roster_evidence.get(club) else roster_evidence[club]["url"],
            "roster_source_tier": "" if not roster_evidence.get(club) else OFFICIAL,
            "roster_status_note": "" if not roster_evidence.get(club) else roster_evidence[club]["note"],
            "report_source_url": INJ_URL if club in report_clubs else
            "https://www.nfl.com/schedules/2026/by-week/week-10",
        })
    n_sweep = wcsv("roster_sweep_32.csv", sweep)

    summary = {
        "report_rows": len(inj),
        "clubs_on_report": len(report_clubs),
        "clubs_on_bye": len(bye),
        "clubs_swept": len(sweep),
        "depth_clubs_parsed": len(clubs_with_chart),
        "starters_named_out_with_chart": len(cascade),
        "replacements_named": sum(1 for c in cascade if c["replacement"]),
        "compounding": sum(1 for c in cascade if c["compounding"] == "yes"),
        "announced_starter_rows": sum(1 for a in ann if a["announced_starter"]),
        "availability_rows": n_avail,
        "sweep_rows": n_sweep,
    }
    wjson("availability_summary.json", summary)
    print("availability rows:", n_avail, "cascade rows:", n_casc, "announced:", n_ann,
          "sweep rows:", n_sweep)
    for c in cascade:
        print("  %-3s %-22s -> %-24s %-14s compounding=%s"
              % (c["club"], c["starter"], c["replacement"] or "(none)", c["depth_of_replacement"],
                 c["compounding"]))


if __name__ == "__main__":
    main()

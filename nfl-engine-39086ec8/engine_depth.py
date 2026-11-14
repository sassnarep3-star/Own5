"""Requirement 6 — measure the DEPTH of a replacement, not the fact of one.

"The fact of a replacement" says only that a starter is out. It cannot distinguish:

    QB1 out -> QB2 in          (a rung)
    QB1 out -> QB2 out -> QB3 (two rungs, and the chart may stop there)

The prior desks in this repository recorded the *fact*: a boolean `deficiency`
that was 1 for 7 of 705 chart slots and 0 for the other 698. That variable cannot
rank a game. This module computes, per position slot:

    chart_depth            how many players the club actually lists
    rungs_down             index of the player who must play (0 = starter)
    depth_exhausted        True if the replacement is the LAST published name
    cascade_count          how many players above him are unavailable
    replaced_share         rungs_down / max(1, chart_depth - 1)   in [0,1]
    replacement_tier       STARTER / BACKUP / THIRD_STRING / FOURTH_STRING / EXHAUSTED
    depth_points           a points-of-exposure score, defined below

and, per club and unit, a `unit_depth_index` = the mean of
`rungs_down * availability_weight` over the slots that are actually exposed,
divided by the same mean over the exposure-weighted worst case, so that a club
missing a fourth-string receiver is not scored like a club missing its QB1.

`depth_points` is deliberately a *definition*, not a fit:
    depth_points = sum over exposed slots of (rungs_down * importance_weight)
    importance_weight = 3.0 QB, 2.0 OT/C/EDGE/CB1, 1.5 other OL/LB/S,
                        1.0 WR/RB/TE/DT/other
The weights are declared here, in one place, with the reason for each. They are
NOT calibrated against outcomes, and the engine says so: any number produced from
them is an exposure score, never an expected-points estimate.
"""

import csv
import io

IMPORTANCE = {
    "QB": (3.0, "single point of failure; backup quality varies most"),
    "LT": (2.0, "blind-side protection"),
    "RT": (1.5, "protection"),
    "LG": (1.5, "interior pressure"),
    "RG": (1.5, "interior pressure"),
    "C": (2.0, "snap and protection calls"),
    "EDGE": (2.0, "pass-rush production is concentrated"),
    "DE": (2.0, "pass-rush production is concentrated"),
    "CB": (2.0, "boundary coverage on an island"),
    "S": (1.5, "coverage shells"),
    "SS": (1.5, "coverage shells"),
    "FS": (1.5, "coverage shells"),
    "NB": (1.0, "nickel role"),
    "LB": (1.5, "run fit and coverage"),
    "MLB": (1.5, "run fit and coverage"),
    "WLB": (1.5, "run fit and coverage"),
    "SAM": (1.0, "situational"),
    "OLB": (1.5, "edge/box hybrid"),
    "DL": (1.0, "rotation"),
    "DT": (1.0, "rotation"),
    "NT": (1.0, "rotation"),
    "RUSH": (1.5, "designated pass rusher"),
    "WR": (1.0, "depth is normal at the position"),
    "RB": (1.0, "committee usage is normal"),
    "TE": (1.0, "two-TE usage is normal"),
    "FB": (0.5, "situational"),
}
DEFAULT_IMPORTANCE = 1.0

TIER = {0: "STARTER", 1: "BACKUP", 2: "THIRD_STRING", 3: "FOURTH_STRING"}

HEADER = (
    "club", "unit", "position", "slot", "chart_depth", "rungs_down",
    "replacement", "replaced_players", "depth_exhausted", "cascade_count",
    "replaced_share", "replacement_tier", "importance", "depth_points",
    "chart_url", "chart_unofficial", "source_row_note",
)

UNIT_HEADER = (
    "club", "unit", "slots_published", "slots_exposed", "rungs_down_sum",
    "depth_points", "max_possible_points", "unit_depth_index", "exhausted_slots",
    "chart_url", "chart_unofficial",
)


def importance(position):
    return IMPORTANCE.get(position, (DEFAULT_IMPORTANCE,))[0]


def chart_depth(players):
    """Number of players the club actually lists for the slot."""
    return sum(1 for p in players if str(p).strip())


def exposed_slot(position, players, out_players):
    """Compute one slot's exposure given the players officially listed as OUT.

    `out_players` is the set of players on the official injury report whose game
    status is 'Out'. Only official statuses are accepted; a player merely 'limited'
    or 'questionable' is not treated as unavailable, because the official report
    does not say he will not play.
    """
    listed = [p for p in players if str(p).strip()]
    if not listed:
        return None
    unavailable = [p for p in listed if p in out_players]
    if unavailable:
        first_available = next(
            (i for i, p in enumerate(listed) if p not in out_players), None)
    else:
        first_available = 0
    if first_available is None:
        # Every published name is out. The depth is exhausted and the club must
        # use a player it does not list. Report that as EXHAUSTED, never guess who.
        return {
            "chart_depth": len(listed),
            "rungs_down": len(listed),
            "replacement": "",
            "replaced_players": "; ".join(unavailable),
            "depth_exhausted": "yes",
            "cascade_count": len(unavailable),
            "tier": "EXHAUSTED",
            "note": "every published player at this slot is Out; replacement not published",
        }
    rungs = first_available
    return {
        "chart_depth": len(listed),
        "rungs_down": rungs,
        "replacement": listed[first_available],
        "replaced_players": "; ".join(unavailable),
        "depth_exhausted": "no",
        "cascade_count": len(unavailable),
        "tier": TIER.get(rungs, "FOURTH_STRING"),
        "note": "" if rungs == 0 else "one or more listed starters are Out",
    }


def build_slot_rows(charts, out_by_club):
    rows = []
    for club, chart in sorted(charts.items()):
        outs = set(out_by_club.get(club, []))
        for unit_key, unit_label in (("offense", "Offense"), ("defense", "Defense")):
            slots = chart.get(unit_key) or []
            for slot_i, (position, players) in enumerate(slots, start=1):
                ex = exposed_slot(position, players, outs)
                if ex is None:
                    continue
                imp = importance(position)
                share = (ex["rungs_down"] / max(1, ex["chart_depth"] - 1)
                         if ex["chart_depth"] > 1 else (1.0 if ex["rungs_down"] else 0.0))
                rows.append({
                    "club": club, "unit": unit_label, "position": position,
                    "slot": slot_i,
                    "chart_depth": ex["chart_depth"],
                    "rungs_down": ex["rungs_down"],
                    "replacement": ex["replacement"],
                    "replaced_players": ex["replaced_players"],
                    "depth_exhausted": ex["depth_exhausted"],
                    "cascade_count": ex["cascade_count"],
                    "replaced_share": round(share, 4),
                    "replacement_tier": ex["tier"],
                    "importance": imp,
                    "depth_points": round(ex["rungs_down"] * imp, 3),
                    "chart_url": chart["url"],
                    "chart_unofficial": "yes" if chart.get("disclaimer") else "no",
                    "source_row_note": ex["note"],
                })
    return rows


def build_unit_rows(slot_rows):
    agg = {}
    for r in slot_rows:
        k = (r["club"], r["unit"])
        a = agg.setdefault(k, {"slots": 0, "exposed": 0, "rungs": 0, "pts": 0.0,
                               "max_pts": 0.0, "exhausted": 0, "url": r["chart_url"],
                               "unofficial": r["chart_unofficial"]})
        a["slots"] += 1
        a["rungs"] += r["rungs_down"]
        a["pts"] += r["depth_points"]
        # worst case at the same slot: every listed player above the last is out
        a["max_pts"] += max(0, r["chart_depth"] - 1) * r["importance"]
        if r["rungs_down"]:
            a["exposed"] += 1
        if r["depth_exhausted"] == "yes":
            a["exhausted"] += 1
    out = []
    for (club, unit), a in sorted(agg.items()):
        idx = (a["pts"] / a["max_pts"]) if a["max_pts"] else 0.0
        out.append({
            "club": club, "unit": unit,
            "slots_published": a["slots"], "slots_exposed": a["exposed"],
            "rungs_down_sum": a["rungs"], "depth_points": round(a["pts"], 3),
            "max_possible_points": round(a["max_pts"], 3),
            "unit_depth_index": round(idx, 4),
            "exhausted_slots": a["exhausted"],
            "chart_url": a["url"], "chart_unofficial": a["unofficial"],
        })
    return out


def out_players_by_club(injuries):
    d = {}
    for club, player, _pos, _inj, _prac, status in injuries:
        if status.strip().lower() == "out":
            d.setdefault(club, []).append(player)
    return d


def to_csv(rows, header=HEADER):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=header, lineterminator="\n",
                       extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({rk: r.get(rk, "") for rk in header})
    return buf.getvalue()


def priority_queue(slot_rows, limit=8):
    """Which exposures matter most, ranked by depth_points then importance."""
    live = [r for r in slot_rows if r["rungs_down"]]
    live.sort(key=lambda r: (-r["depth_points"], -r["importance"], r["club"]))
    return live[:limit]

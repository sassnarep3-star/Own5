"""Depth of a replacement, measured - not the fact that somebody is next up.

The requirement this file exists to satisfy is precise: tracking *that* a starter
was replaced tells a bettor nothing; tracking *how deep* the replacement is tells
them almost everything. So depth here is a measured quantity, not a name.

For every position group on every club's published depth chart:

``listed_replacements``   how many names the club publishes behind the first string
                          (official club depth-chart page, transcribed and vendored).
``second_string_snaps``   the career-of-this-season snaps that second-string player
                          has actually taken in 2026 (measured from the NFL's own
                          play records, mirrored).
``second_string_share``   their median share of the unit's snaps in the games they
                          appeared in.
``starter_to_second_gap`` the difference in median snap share between first and second
                          string: how much load the unit has to absorb, not how much
                          it has to *find*.
``depth_grade``           TESTED / PARTIALLY TESTED / UNTESTED / NO NAME PUBLISHED,
                          from the two measured numbers above by fixed rules stated
                          in ``data/depth_rules.csv``.
``peer_deficiency_points``  the earlier session's published deficiency estimate, kept
                          in its own column, labelled as another model's output and
                          never blended into the measurement.

Why "UNTESTED" is not an insult to the player: a second-stringer with 40 snaps in
nine weeks has no evidence behind them either way. The desk's position is that an
absence at that position is unpriceable from this data, which is a different claim
from "the line should move", and it is written that way.
"""
from __future__ import annotations

import csv
import os
import re

import statslib as st
import availability

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
CHART = os.path.join(HERE, "pinned", "depth_charts_2026_11_13.csv")

TESTED_SHARE = 0.50      # median snap share of the unit's snaps in games played
TESTED_GAMES = 3         # games with snaps at all in 2026
PARTIAL_GAMES = 1


def _name(s):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z ]", "", (s or "").lower())).strip()


def snap_profile(weeks=range(1, 10)):
    """team -> exact name -> dict(games, shares, position)."""
    snaps = availability.snaps_by_week("2026")
    prof = {}
    for (team, wk), players in snaps.items():
        if wk not in weeks:
            continue
        for key, (sn, pct, pos, disp) in players.items():
            if key == "__near__":
                continue
            d = prof.setdefault(team, {}).setdefault(key, dict(disp=disp, pos=pos, games=0, shares=[],
                                                                snaps=0.0))
            d["games"] += 1
            d["shares"].append(pct)
            d["snaps"] += sn
    return prof


def measure():
    prof = snap_profile()
    rows = []
    for r in csv.DictReader(open(CHART, newline="", encoding="utf-8")):
        team = (r.get("team") or "").strip()
        unit = (r.get("unit") or "").strip()
        pos = (r.get("position") or "").strip()
        first = (r.get("first_string") or "").strip()
        second = (r.get("second_string") or "").strip()
        third = (r.get("third_string") or "").strip()
        published = int(r.get("players_published") or 0)

        def look(nm):
            if not nm:
                return None
            d = prof.get(team, {}).get(_name(nm))
            if not d:
                return dict(games=0, share=None, snaps=0.0, matched=False)
            return dict(games=d["games"], share=st.median([x for x in d["shares"] if x > 0])
                        if any(x > 0 for x in d["shares"]) else None,
                        snaps=d["snaps"], matched=True)

        f1, f2, f3 = look(first), look(second), look(third)
        gap = ""
        if f1 and f1["share"] and f2 and f2["share"]:
            gap = round(f1["share"] - f2["share"], 4)
        if not second:
            grade = "NO NAME PUBLISHED"
        elif f2 is None or not f2["matched"]:
            grade = "UNTESTED (no 2026 snaps in the play records)"
        elif (f2["share"] or 0) >= TESTED_SHARE and f2["games"] >= TESTED_GAMES:
            grade = "TESTED"
        elif f2["games"] >= PARTIAL_GAMES:
            grade = "PARTIALLY TESTED"
        else:
            grade = "UNTESTED (no 2026 snaps in the play records)"
        rows.append(dict(team=team, club=r.get("club", ""), unit=unit, position=pos,
                         first_string=first or "", second_string=second or "", third_string=third or "",
                         listed_replacements=max(0, published - 1) if published else "",
                         players_published=published,
                         first_string_games=f1["games"] if f1 else "",
                         first_string_share="" if not (f1 and f1["share"]) else round(f1["share"], 4),
                         second_string_games=f2["games"] if f2 else "",
                         second_string_share="" if not (f2 and f2["share"]) else round(f2["share"], 4),
                         second_string_snaps_2026=round(f2["snaps"], 0) if f2 else "",
                         third_string_games=f3["games"] if f3 else "",
                         third_string_share="" if not (f3 and f3["share"]) else round(f3["share"], 4),
                         starter_to_second_gap=gap,
                         depth_grade=grade,
                         no_backup_published=r.get("no_backup_published", ""),
                         expected_starter_next_game=r.get("expected_starter_next_game", ""),
                         peer_deficiency_points=r.get("deficiency_points", ""),
                         tier="OFFICIAL club depth chart (vendored) x mirrored play records; "
                              "peer deficiency column belongs to session 864d5668",
                         source=r.get("source", ""),
                         note=("a replacement with no measured snaps is not a weak replacement, it is an "
                               "unpriced one" if grade.startswith("UNTESTED") else
                               ("the club published no second name at this position" if grade.startswith("NO")
                                else ""))))
    return rows


def rollup(rows):
    """Team-level depth: the position groups a club cannot cover if its starter is out."""
    per = {}
    for r in rows:
        d = per.setdefault(r["team"], dict(groups=0, tested=0, partial=0, untested=0, none=0,
                                            gap_sum=[], no_backup=0))
        d["groups"] += 1
        g = r["depth_grade"]
        if g == "TESTED":
            d["tested"] += 1
        elif g == "PARTIALLY TESTED":
            d["partial"] += 1
        elif g.startswith("UNTESTED"):
            d["untested"] += 1
        else:
            d["none"] += 1
        if r["starter_to_second_gap"] != "":
            d["gap_sum"].append(float(r["starter_to_second_gap"]))
        if str(r["no_backup_published"]) == "yes":
            d["no_backup"] += 1
    out = []
    for team in sorted(per):
        d = per[team]
        out.append(dict(team=team, position_groups=d["groups"], tested=d["tested"],
                        partially_tested=d["partial"], untested=d["untested"],
                        no_name_published=d["none"],
                        pct_groups_tested=round(100.0 * d["tested"] / max(1, d["groups"]), 1),
                        mean_starter_to_second_gap=round(st.median(d["gap_sum"]), 4) if d["gap_sum"] else "",
                        groups_with_no_backup_published=d["no_backup"],
                        note="counts of measured depth, by fixed rules in depth_rules.csv; "
                             "a low 'tested' count is a warning about what the desk cannot price"))
    return out


def rules():
    return [dict(rule="TESTED", definition=f"second string has median snap share >= {TESTED_SHARE} "
                                           f"of the unit's snaps in >= {TESTED_GAMES} games of 2026"),
              dict(rule="PARTIALLY TESTED", definition=f"second string appeared in >= {PARTIAL_GAMES} "
                                                        "game but below the TESTED thresholds"),
              dict(rule="UNTESTED", definition="second string has no snaps in the 2026 play records "
                                                "(injury, healthy scratch, practice squad, or a name the "
                                                "two sources spell differently)"),
              dict(rule="NO NAME PUBLISHED", definition="the club's depth chart lists no second string "
                                                        "at that position"),
              dict(rule="join", definition="names are matched exactly after normalisation; no fuzzy "
                                            "matching is used anywhere in this file"),
              dict(rule="peer column", definition="deficiency_points is another session's model output, "
                                                   "published unchanged in its own column and never combined "
                                                   "with the measured columns")]


def write():
    rows = measure()
    cols = list(rows[0].keys())
    with open(os.path.join(DATA, "replacement_depth.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    ru = rollup(rows)
    with open(os.path.join(DATA, "depth_by_team.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(ru[0].keys()))
        w.writeheader()
        w.writerows(ru)
    with open(os.path.join(DATA, "depth_rules.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["rule", "definition"])
        w.writeheader()
        w.writerows(rules())
    # the pairing the requirement actually asks for: absence x depth at that position
    impact = list(csv.DictReader(open(os.path.join(DATA, "availability_impact.csv"), newline="", encoding="utf-8")))
    by_team_pos = {}
    for r in rows:
        by_team_pos.setdefault((r["team"], r["position"]), []).append(r)
    pairs = []
    for r in impact:
        for chunk in r["detail"].split(" | "):
            mm = re.match(r"^(.*?) \((.*?), (.*?)\): (.*)$", chunk)
            if not mm:
                continue
            player, pos, status, rest = mm.groups()
            grp = by_team_pos.get((r["team"], pos), [])
            g = grp[0] if grp else None
            pairs.append(dict(team=r["team"], position=pos, player_out=player,
                              status_or_practice=status,
                              measured_removal=rest.split(" -> ")[0],
                              replacement_named=rest.split(" -> ")[1] if " -> " in rest else "",
                              depth_grade=(g["depth_grade"] if g else "NO DEPTH-CHART ROW for this position"),
                              starter_to_second_gap=(g["starter_to_second_gap"] if g else ""),
                              listed_replacements=(g["listed_replacements"] if g else ""),
                              tier="OFFICIAL chart x OFFICIAL report x mirrored play records",
                              source=(g["source"] if g else availability.INJ_URL),
                              note=("the tradable question is not whether the starter is out, it is whether "
                                    "the next man has ever carried the load - these two columns answer it")))
    with open(os.path.join(DATA, "absence_vs_depth.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(pairs[0].keys()))
        w.writeheader()
        w.writerows(pairs)
    grades = {}
    for r in rows:
        grades[r["depth_grade"].split(" (")[0]] = grades.get(r["depth_grade"].split(" (")[0], 0) + 1
    return dict(groups=len(rows), teams=len(ru), pairs=len(pairs), grades=grades)


if __name__ == "__main__":
    print(write())

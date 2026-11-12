#!/usr/bin/env python3
"""Join official Week 10 injury report x official club depth charts.

Produces deficiencies_2026_wk10.csv:
  one row per (team, position) where the listed starter(s) carry an injury
  designation, identifying the next-man-up string level (2/3/4/none).

Rules:
  - Never infer: replacement is only the next listed name from the official
    depth chart; if no backup is listed, replacement is blank + flagged.
  - HOU has no machine-readable depth chart (image-only) -> excluded and
    flagged in flagged_items.csv by the caller.
"""
import csv
import os
import re
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")

def norm(name: str) -> str:
    if not name:
        return ""
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    s = s.lower()
    s = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b\.?", "", s)
    s = re.sub(r"[^a-z ]", "", s)
    return re.sub(r"\s+", " ", s).strip()

def severity(row):
    gs = (row.get("game_status") or "").strip()
    ps = (row.get("practice_status") or "").strip()
    if gs == "Out":
        return 4, "Out"
    if gs == "Questionable":
        return 3, "Questionable"
    if ps == "Did Not Participate In Practice":
        return 3, "DNP"
    if ps == "Limited Participation in Practice":
        return 2, "Limited"
    if ps == "Full Participation in Practice":
        return 1, "Full (listed on report)"
    return 0, "Unknown"

def main():
    with open(os.path.join(DATA, "depth_charts_2026_wk10.csv")) as f:
        depth = list(csv.DictReader(f))
    with open(os.path.join(DATA, "injuries_2026_wk10.csv")) as f:
        injuries = list(csv.DictReader(f))

    # index: (team, norm_player) -> list of depth rows where player is a listed starter
    starters = {}
    for d in depth:
        cell = d["starter"].strip()
        if not cell:
            continue
        parts = re.split(r"\band\b|,|\[.*?\]\(.*?\)", cell)
        for p in parts:
            p = p.strip()
            if not p:
                continue
            starters.setdefault((d["team"], norm(p)), []).append(d)

    # injury status by (team, norm_player) for replacement-chain awareness
    inj_status = {}
    for inj in injuries:
        sev, lab = severity(inj)
        key = (inj["team"], norm(inj["player"]))
        if key not in inj_status or sev > inj_status[key][0]:
            inj_status[key] = (sev, lab)

    out_rows = []
    matched = set()
    for inj in injuries:
        key = (inj["team"], norm(inj["player"]))
        if key not in starters:
            continue
        sev_label = severity(inj)
        sev, lab = sev_label
        if sev < 2:  # only Limited / DNP / Questionable / Out are deficiencies
            continue
        for d in starters[key]:
            # next-man-up: first non-empty backup cell after starter
            replacement, level = "", ""
            for col, lv in (("second", "2nd"), ("third", "3rd"), ("fourth", "4th")):
                if d[col].strip():
                    # exclude the injured starter if he is also listed as his own backup
                    backups = [b for b in re.split(r"\band\b|,", d[col]) if b.strip()]
                    backups = [b for b in backups if norm(b) != norm(inj["player"])]
                    if backups:
                        replacement, level = "; ".join(b.strip() for b in backups), lv
                        break
            if not replacement:
                level = "none"
            # effective next man up: walk strings in order, skipping players
            # officially listed Out (game_status). Computed only from official
            # lists -- no inference about who will actually play.
            eff, eff_level = "", ""
            for col, lv in (("second", "2nd"), ("third", "3rd"), ("fourth", "4th")):
                if not d[col].strip():
                    continue
                backups = [b.strip() for b in re.split(r"\band\b|,", d[col]) if b.strip()]
                backups = [b for b in backups if norm(b) != norm(inj["player"])]
                if not backups:
                    continue
                avail = [b for b in backups if inj_status.get((inj["team"], norm(b)), (0, ""))[0] < 4]
                if avail:
                    eff, eff_level = "; ".join(avail), lv
                    break
                # all listed backups are Out -> keep looking deeper
            if level != "none" and eff_level and eff_level != level:
                eff_note = f"skips Out {replacement}"
            else:
                eff_note = ""
            # is the next man up himself on the injury report (severity>=2)?
            repl_flag = ""
            if replacement:
                for rb in re.split(r"\band\b|;", replacement):
                    st = inj_status.get((inj["team"], norm(rb)))
                    if st and st[0] >= 2:
                        repl_flag = f"replacement {rb.strip()} is {st[1]}"
                        break
            out_rows.append({
                "team": inj["team"],
                "unit": d["unit"],
                "position": d["position"],
                "starter": d["starter"],
                "injured_player": inj["player"],
                "position_reported": inj["position"],
                "injury": inj["injury"],
                "practice_status": inj["practice_status"],
                "game_status": inj["game_status"],
                "severity": lab,
                "replacement": replacement,
                "replacement_string": level,
                "replacement_injured": repl_flag,
                "effective_replacement": eff,
                "effective_string": eff_level or ("none" if not eff else eff_level),
                "effective_note": eff_note,
                "game": inj["game"],
                "depth_source_url": d["source_url"],
                "injury_source_url": inj["source_url"],
            })
            matched.add((inj["team"], inj["player"]))

    # sort: severity desc, team
    order = {"Out": 0, "Questionable": 1, "DNP": 2, "Limited": 3, "Full (listed on report)": 4}
    out_rows.sort(key=lambda r: (order.get(r["severity"], 9), r["team"], r["unit"], r["position"]))

    dest = os.path.join(DATA, "deficiencies_2026_wk10.csv")
    with open(dest, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        w.writeheader()
        w.writerows(out_rows)

    print(f"wrote {len(out_rows)} deficiency rows; matched injuries on depth-chart starters: {len(matched)}")
    for r in out_rows:
        if r["severity"] in ("Out", "Questionable", "DNP"):
            print(f"  [{r['severity']:>13}] {r['team']} {r['position']:<5} starter={r['injured_player']:<22} -> {r['replacement_string']} string: {r['replacement'] or 'NO LISTED BACKUP'}")

if __name__ == "__main__":
    main()

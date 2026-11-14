"""Availability: who is actually unavailable, and what removing them is worth.

Three questions, deliberately kept apart
----------------------------------------
``base rates``  - when the league report says a status, what happened historically?
                  Measured, not assumed: each reported status is joined to whether
                  that player appears in the game's snap records.
``counts``      - what does the current week's official report actually say? Listed
                  per club, with no prediction attached.
``impact``      - for a specific club, how large a role is being removed, and has
                  the next man ever carried a comparable one?

Why they must stay apart: a 61.6% "Questionable played" rate is a league-wide base
rate across hundreds of player-weeks. Applying it to one player's hamstring is a
category error, and it is the error that makes most injury models unfalsifiable. So
the impact table never says "X will play"; it says "the report lists X as Out, and
X's role was 78% of the team's offensive snaps, and the most-used player at that
position without X has carried 12%". A reviewer can price that.

Tier honesty
------------
Report status and practice participation come from the league's official injury
report, transcribed and vendored (``pinned/injuries_wk10_official.csv``, one URL
per row). Snap counts come from the pinned mirror of the NFL's own play records
and are AGGREGATOR tier. Where the official report and the mirror disagree on the
same week, both counts are published in ``data/availability_source_diff.csv`` and
neither is preferred silently.
"""
from __future__ import annotations

import csv
import os
import re

import statslib as st
import inputs

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OFFICIAL_INJ = os.path.join(HERE, "pinned", "injuries_wk10_official.csv")
INJ_URL = "https://www.nfl.com/injuries/league/2026/reg10"
AMBIGUOUS = [0]        # rejected near-match joins; published with the base rates
SNAP_URL = "https://github.com/nflverse/nflverse-data/releases/tag/snap_counts"
INJ_URL_NV = "https://github.com/nflverse/nflverse-data/releases/tag/injuries"

# snap fields a position is judged on: defence on defence_snaps, everything else
# on offence, specialists on special teams plus their own side
DEF_POS = {"DE", "DT", "NG", "NT", "LB", "OLB", "ILB", "MLB", "CB", "NB", "SS", "FS", "S", "DB"}


def _snap_of(row):
    pos = (row.get("position") or "").strip().upper()
    def _f(k):
        try:
            return float(row.get(k) or 0)
        except ValueError:
            return 0.0
    off, dfn, sp = _f("offense_snaps"), _f("defense_snaps"), _f("st_snaps")
    offp, dfp, spp = _f("offense_pct"), _f("defense_pct"), _f("st_pct")
    if pos in DEF_POS:
        return dfn, dfp
    if off == 0 and dfn == 0 and sp > 0:
        return sp, spp
    return (off, offp) if off >= dfn else (dfn, dfp)


def _name(s):
    """Exact join key. Deliberately strict.

    A looser key (surname + first initial) looks harmless and quietly creates
    phantom appearances: two different players can share it, and an "Out" player
    who did not play then appears in the snap records as somebody else. Joining
    on the exact normalised full name cannot create that error, and the number of
    rejected near-matches is published so the residual risk is visible rather than
    assumed away.
    """
    return re.sub(r"\s+", " ", re.sub(r"[^a-z ]", "", (s or "").lower())).strip()


def snaps_by_week(season="2026"):
    """(team, week) -> {exact normalised name: (snaps, pct, position, display_name)}.

    Also fills ``LOOSE``: (team, week) -> {surname + first initial: [exact names]}, so
    a caller can count how many rejected near-matches exist. The join is strict on
    purpose; the ambiguity it refuses to resolve is reported, not hidden.
    """
    out = {}
    loose = {}
    for r in inputs.read_gz_csv(inputs.PINNED[f"nflverse_snap_counts_{season}"]):
        try:
            wk = int(r.get("week") or 0)
        except ValueError:
            continue
        snaps, pct = _snap_of(r)
        if snaps <= 0:
            continue
        team = (r.get("team") or "").strip()
        d = out.setdefault((team, wk), {})
        key = _name(r.get("player"))
        if key in d:      # two rows for one player in one game: sum, keep the larger share
            d[key] = (d[key][0] + snaps, max(d[key][1], pct), r.get("position", ""), r.get("player", ""))
        else:
            d[key] = (snaps, pct, r.get("position", ""), r.get("player", ""))
        parts = key.split()
        lk = (parts[-1] + " " + parts[0][0]) if len(parts) >= 2 else key
        L = loose.setdefault((team, wk), {})
        names = L.setdefault(lk, [])
        if key not in names:
            names.append(key)
    LOOSE.clear()
    LOOSE.update(loose)
    return out


LOOSE = {}


def team_snap_totals(snaps):
    """Team offensive/defensive snap totals, derived from the players' own rows."""
    tot = {}
    for (team, wk), players in snaps.items():
        off = dfn = 0.0
        for snaps_v, pct, pos, _ in players.values():
            if pct <= 0:
                continue
            est = snaps_v / pct
            if (pos or "").upper() in DEF_POS:
                dfn = max(dfn, est)
            else:
                off = max(off, est)
        d = tot.setdefault((team, wk), dict(off=0.0, defn=0.0))
        d["off"] = max(d["off"], off)
        d["defn"] = max(d["defn"], dfn)
    return tot


def base_rates(season="2026", max_week=9):
    """Reported status -> observed availability, measured on weeks 1-9."""
    snaps = snaps_by_week(season)
    tally = {}
    for r in inputs.injuries(seasons=(season,)):
        try:
            wk = int(r.get("week") or 0)
        except ValueError:
            continue
        if wk > max_week:
            continue
        status = (r.get("report_status") or "").strip()
        if not status:
            continue
        t = tally.setdefault(status, dict(n=0, played=0, shares=[], unique_rejected=0,
                                           ambiguous_rejected=0))
        t["n"] += 1
        rec = snaps.get((r.get("team", ""), wk), {}).get(_name(r.get("full_name")))
        if rec is None:
            # not joined: was there a *candidate* the strict key refused? Published per
            # status so the reader can judge how much of the rate is join fragility.
            parts = _name(r.get("full_name")).split()
            lk = (parts[-1] + " " + parts[0][0]) if len(parts) >= 2 else ""
            cands = LOOSE.get((r.get("team", ""), wk), {}).get(lk, [])
            if len(cands) == 1:
                t["unique_rejected"] += 1
            elif len(cands) > 1:
                t["ambiguous_rejected"] += 1
        if rec:
            t["played"] += 1
            t["shares"].append(rec[1])
    rows = []
    for status in sorted(tally, key=lambda s: -tally[s]["n"]):
        t = tally[status]
        n, k = t["n"], t["played"]
        ur, ar = t["unique_rejected"], t["ambiguous_rejected"]
        lo, hi = st.wilson_ci(k, n)
        rows.append(dict(status=status, n_player_weeks=n, played=k,
                         played_rate=round(k / n, 4) if n else "",
                         wilson_lo=round(lo, 4), wilson_hi=round(hi, 4),
                         median_snap_share_when_played=round(st.median(t["shares"]), 4) if t["shares"] else "",
                         join_rejected_unique_candidate=ur, join_rejected_ambiguous=ar,
                         tier="MEASURED: official report x NFL play records (pinned mirror)",
                         source=INJ_URL_NV,
                         note=(f"a league-wide base rate for the status; it is not a statement about any "
                               f"individual player, and is never multiplied into a player's projection. "
                               f"{ur} report rows named a player who could not be matched exactly to that "
                               f"week's snap records although one same-team candidate existed (spelling "
                               f"differences between the two sources), so the rate is a lower bound on "
                               f"availability; {ar} rows were refused because two or more candidates shared "
                               f"a surname and initial")))
    return rows


def official_wk10():
    """What the current official report says, per club. Counts only, no modelling."""
    rows = list(csv.DictReader(open(OFFICIAL_INJ, newline="", encoding="utf-8")))
    per = {}
    for r in rows:
        team = (r.get("team") or "").strip()
        if not team:
            continue
        d = per.setdefault(team, dict(n=0, players=set(), prac={}, stat={}, pos={}))
        d["n"] += 1
        d["players"].add((r.get("player") or "").strip())
        p = (r.get("practice_status_as_published") or "").strip() or "(nothing published)"
        d["prac"][p] = d["prac"].get(p, 0) + 1
        s = (r.get("game_status_as_published") or "").strip() or "(no game status published yet)"
        d["stat"][s] = d["stat"].get(s, 0) + 1
        pos = (r.get("position") or "?").strip()
        d["pos"][pos] = d["pos"].get(pos, 0) + 1
    out = []
    for team in sorted(per):
        d = per[team]
        out.append(dict(team=team, rows_listed=d["n"], distinct_players=len(d["players"]),
                        practice_participation="; ".join(f"{k}: {v}" for k, v in sorted(d["prac"].items())),
                        game_status="; ".join(f"{k}: {v}" for k, v in sorted(d["stat"].items())),
                        positions="; ".join(f"{k}: {v}" for k, v in sorted(d["pos"].items())),
                        tier="OFFICIAL (league injury report, transcribed and vendored)",
                        source=rows[0].get("source") or INJ_URL,
                        note=("the report is published on a fixed weekly schedule; a blank game status "
                              "means the club had not filed one at capture time, not that the player is "
                              "available")))
    return out


def source_diff():
    """Official report vs the mirror's feed for the same week: both counts, no merging."""
    off = list(csv.DictReader(open(OFFICIAL_INJ, newline="", encoding="utf-8")))
    per_off = {}
    for r in off:
        t = (r.get("team") or "").strip()
        per_off[t] = per_off.get(t, 0) + 1
    per_nv = {}
    for r in inputs.injuries(week=10, seasons=("2026",)):
        t = (r.get("team") or "").strip()
        per_nv[t] = per_nv.get(t, 0) + 1
    rows = []
    for t in sorted(set(per_off) | set(per_nv)):
        a, b = per_off.get(t, 0), per_nv.get(t, 0)
        rows.append(dict(team=t, official_rows=a, mirror_rows=b, difference=a - b,
                         result="MATCH" if a == b else "DISAGREE",
                         official_url=(off[0].get("source") or INJ_URL), mirror_url=INJ_URL_NV,
                         note=("the official report lists every player a club files, including players "
                               "the mirror drops; a difference here is a scope difference, not an error, "
                               "and both counts are published rather than one being chosen")))
    to, tn = sum(per_off.values()), sum(per_nv.values())
    rows.append(dict(team="LEAGUE TOTAL", official_rows=to, mirror_rows=tn, difference=to - tn,
                     result="MATCH" if to == tn else "DISAGREE",
                     official_url=(off[0].get("source") or INJ_URL), mirror_url=INJ_URL_NV,
                     note="flag MK-F-06: row counts differ between the two tiers for the same week"))
    return rows, to, tn


def squad_impact(week=10, lookback=3):
    """Expected snaps removed and who is left holding them."""
    snaps = snaps_by_week("2026")
    totals = team_snap_totals(snaps)
    weeks = [w for w in range(week - 1, week - 1 - lookback, -1) if w >= 1]
    role = {}
    for (team, wk), players in snaps.items():
        if wk not in weeks:
            continue
        for key, (sn, pct, pos, disp) in players.items():
            d = role.setdefault((team, key), dict(pos=pos, disp=disp, off=[], defn=[], seen=0))
            if (pos or "").upper() in DEF_POS:
                d["defn"].append(pct)
            else:
                d["off"].append(pct)
            d["seen"] += 1
    side_snaps = {}
    for (team, wk), v in totals.items():
        side_snaps.setdefault(team, {"off": [], "defn": []})
        side_snaps[team]["off"].append(v["off"] or 1.0)
        side_snaps[team]["defn"].append(v["defn"] or 1.0)
    base = {t: {side: (sum(v) / len(v) if v else 1.0) for side, v in d.items()}
            for t, d in side_snaps.items()}

    absent = {}
    for r in csv.DictReader(open(OFFICIAL_INJ, newline="", encoding="utf-8")):
        stat = (r.get("game_status_as_published") or "").strip()
        prac = (r.get("practice_status_as_published") or "").strip()
        t, p = (r.get("team") or "").strip(), (r.get("player") or "").strip()
        if not t or not p:
            continue
        keeps_out = stat in ("Out", "Doubtful", "Reserve", "Injured Reserve") or prac.startswith("Did Not")
        if keeps_out:
            absent.setdefault(t, []).append(dict(player=p, position=(r.get("position") or "?").strip(),
                                                 status=stat, practice=prac,
                                                 injury=r.get("injury") or ""))
    rows = []
    for team in sorted(absent):
        lost = lost_off = lost_def = 0.0
        unknown_side = 0
        details = []
        for pl in absent[team]:
            key = _name(pl["player"])
            d = role.get((team, key))
            is_def = (pl["position"] or "").upper() in DEF_POS
            side = "defn" if is_def else "off"
            shares = []
            if d:
                # the share is always taken against the player's own unit, so an
                # offensive line and a secondary are never divided by the same base
                shares = (d["defn"] if is_def else d["off"]) or (d["off"] or d["defn"])
                share = st.median([x for x in shares if x > 0]) if any(shares) else 0.0
                lost_snaps = share * base.get(team, {}).get(side, 0.0)
                lost += lost_snaps
                if is_def:
                    lost_def += lost_snaps
                else:
                    lost_off += lost_snaps
                measured = (f"median snap share {share:.3f} of the {'defence' if is_def else 'offence'} "
                            f"snap base over {len(shares)} listed weeks; about {lost_snaps:.0f} snaps")
            else:
                share = None
                unknown_side += 1
                measured = ("not in the snap records for the last three weeks (not played, or the mirror "
                            "spells the name differently) - snaps removed left blank, never assumed")
            mate = None
            pos_group = (pl["position"] or "").upper()
            pool = []
            for (tc, kk), v in role.items():
                if tc != team:
                    continue
                if (v["pos"] or "").upper() != pos_group or kk == key:
                    continue
                sh = st.median([s for s in (v["off"] or v["defn"]) if s > 0]) if any(
                    [s for s in (v["off"] or v["defn"]) if s > 0]) else 0.0
                if sh > 0:
                    pool.append((v["disp"], sh))
            pool.sort(key=lambda x: -x[1])
            if pool:
                mate = f"{pool[0][0]} at {pool[0][1]:.3f} snap share"
                depth_after = len(pool)
            else:
                mate = "NO MEASURED BACKUP at this position in the snap records"
                depth_after = 0
            details.append(dict(pl, share=share, measured=measured, mate=mate, backups_measured=depth_after))
        b = base.get(team, {})
        measured_any = any(d["share"] is not None for d in details)
        # Published-first arithmetic: round the snap counts, then derive each
        # percentage from the *rounded* numbers, so a reader holding only this row can
        # reproduce every figure in it. Percentages computed from unrounded internals
        # are correct and unauditable at the same time.
        so = round(lost_off, 1) if measured_any else None
        sd = round(lost_def, 1) if measured_any else None
        bo = round(b.get("off", 0.0), 1)
        bd = round(b.get("defn", 0.0), 1)
        po = round(100.0 * so / max(1e-9, bo), 2) if so is not None else None
        pd_ = round(100.0 * sd / max(1e-9, bd), 2) if sd is not None else None
        rows.append(dict(team=team, week=week, players_kept_out=len(absent[team]),
                         players_unmatched=unknown_side,
                         expected_snaps_removed=(round((so or 0.0) + (sd or 0.0), 1)
                                                 if measured_any else ""),
                         snaps_removed_offence="" if so is None else so,
                         snaps_removed_defence="" if sd is None else sd,
                         pct_of_offence_snap_base="" if po is None else po,
                         pct_of_defence_snap_base="" if pd_ is None else pd_,
                         offence_snap_base=bo,
                         defence_snap_base=bd,
                         detail=" | ".join(f"{d['player']} ({d['position']}, {d['status'] or d['practice']}): "
                                           f"{d['measured']} -> {d['mate']}" for d in details),
                         tier="OFFICIAL report x mirrored play records",
                         source=INJ_URL,
                         note=("snaps removed, not points: the points question is answered in depth.py and "
                               "labelled separately there. Each side's percentage is against that side's "
                               "own snap base, never a blend; it can still exceed 100 when several "
                               "full-time players at one position are out, because a snap is not a slot - "
                               "the column measures volume removed, not a share of a budget. "
                               "players_unmatched are on the report but absent from the snap records, so "
                               "they contribute zero rather than an estimate")))
    return rows


def write():
    br = base_rates()
    with open(os.path.join(DATA, "availability_base_rates.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(br[0].keys()))
        w.writeheader()
        w.writerows(br)
    oc = official_wk10()
    with open(os.path.join(DATA, "availability_wk10_official.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(oc[0].keys()))
        w.writeheader()
        w.writerows(oc)
    sd, to, tn = source_diff()
    with open(os.path.join(DATA, "availability_source_diff.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(sd[0].keys()))
        w.writeheader()
        w.writerows(sd)
    si = squad_impact()
    cols = ["team", "week", "players_kept_out", "players_unmatched", "expected_snaps_removed",
            "snaps_removed_offence", "snaps_removed_defence", "offence_snap_base", "defence_snap_base",
            "pct_of_offence_snap_base", "pct_of_defence_snap_base",
            "detail", "tier", "source", "note"]
    with open(os.path.join(DATA, "availability_impact.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in si:
            w.writerow({k: r.get(k, "") for k in cols})
    return dict(base_rate_rows=len(br), clubs_official=len(oc), official_rows=to, mirror_rows=tn,
                impact_rows=len(si))


if __name__ == "__main__":
    print(write())

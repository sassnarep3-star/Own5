#!/usr/bin/env python3
"""Deterministic roll-up: row-level injury CSVs -> per-club views + delta.

Run from repo root:  python3 nfl-teamview-42899de4/compute_views.py
Outputs (byte-stable, CI diffs them):
  data/nfl-teamview-42899de4/team_view_w11.csv
  data/nfl-teamview-42899de4/team_view_w10.csv
  data/nfl-teamview-42899de4/team_delta_w10_w11.csv
Rules:
  * Designation counts are BLANK (never 0) when the official report has not
    printed game statuses for that club's game (F-TV-03).
  * BYE clubs are not on the report: every report column is BLANK (F-TV-06).
  * 'No Injuries Reported' clubs: players_listed=0 and designations 0 because
    the page states it explicitly (not inferred).
  * starters_out / replacement_named are always BLANK (F-TV-01/02).
"""
import csv
from pathlib import Path

DATA = Path("data/nfl-teamview-42899de4")
SRC11 = "https://www.nfl.com/injuries/league/2026/reg11"
SRC10 = "https://www.nfl.com/injuries/league/2026/reg10"

CLUB_NAMES = {
    "ATL": "Atlanta Falcons", "ARI": "Arizona Cardinals", "AZ": "Arizona Cardinals",
    "BAL": "Baltimore Ravens", "BUF": "Buffalo Bills", "CAR": "Carolina Panthers",
    "CHI": "Chicago Bears", "CIN": "Cincinnati Bengals", "CLE": "Cleveland Browns",
    "DAL": "Dallas Cowboys", "DEN": "Denver Broncos", "DET": "Detroit Lions",
    "GB": "Green Bay Packers", "HOU": "Houston Texans", "IND": "Indianapolis Colts",
    "JAX": "Jacksonville Jaguars", "KC": "Kansas City Chiefs", "LAC": "Los Angeles Chargers",
    "LAR": "Los Angeles Rams", "LV": "Las Vegas Raiders", "MIA": "Miami Dolphins",
    "MIN": "Minnesota Vikings", "NE": "New England Patriots", "NO": "New Orleans Saints",
    "NYG": "New York Giants", "NYJ": "New York Jets", "PHI": "Philadelphia Eagles",
    "PIT": "Pittsburgh Steelers", "SEA": "Seattle Seahawks", "SF": "San Francisco 49ers",
    "TB": "Tampa Bay Buccaneers", "TEN": "Tennessee Titans", "WAS": "Washington Commanders",
}


def read_csv(name):
    with open(DATA / name, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def club_report_state(rows):
    """Return (state, player_rows). state in listed|no_injuries_reported|absent."""
    if not rows:
        return "absent", []
    if all(r["row_type"] == "no_injuries_reported" for r in rows):
        return "no_injuries_reported", []
    return "listed", [r for r in rows if r["row_type"] == "player"]


def summarize(rows):
    """Counts from player rows. designations may be 'not printed'."""
    dnp = sum(1 for r in rows if r["practice_status"] == "Did Not Participate In Practice")
    lp = sum(1 for r in rows if r["practice_status"] == "Limited Participation in Practice")
    fp = sum(1 for r in rows if r["practice_status"] == "Full Participation in Practice")
    out = sum(1 for r in rows if r["game_status"] == "Out")
    q = sum(1 for r in rows if r["game_status"] == "Questionable")
    d = sum(1 for r in rows if r["game_status"] == "Doubtful")
    printed = (out + q + d) > 0  # see module docstring heuristic
    qb = [f"{r['player']} ({r['practice_status']})" for r in rows if r["position"] == "QB"]
    return {
        "listed": len(rows), "dnp": dnp, "lp": lp, "fp": fp,
        "out": out, "q": q, "d": d, "printed": printed,
        "net": out + q + d, "qb": "; ".join(qb),
    }


def week_fixtures(week):
    fx = read_csv(f"fixtures_w{week}.csv")
    opp = {}
    meta = {}
    for g in fx:
        opp[g["away"]] = (g["home"], g)
        opp[g["home"]] = (g["away"], g)
        for c in (g["away"], g["home"]):
            meta[c] = g
    return opp, meta


def build_week(week, src, read_utc_default):
    _, fx_meta = week_fixtures(week)
    byes = {r["club"] for r in read_csv("byes.csv") if r["week"] == str(week)}
    report = read_csv(f"injury_report_w{week}.csv")
    clubs = sorted(set(fx_meta) | byes)
    out_rows = []
    for club in clubs:
        crows = [r for r in report if r["club"] == club]
        state, prows = club_report_state(crows)
        base = {
            "club": club,
            "club_name": CLUB_NAMES[club],
            "week": str(week),
            "status": "BYE" if club in byes else "PLAYING",
            "opponent": fx_meta.get(club, {}).get("away" if fx_meta.get(club, {}).get("home") == club else "home", ""),
            "kickoff_printed": fx_meta.get(club, {}).get("kickoff_printed", ""),
            "network": fx_meta.get(club, {}).get("network", fx_meta.get(club, {}).get("slot", "")),
            "report_state": state,
            "starters_out": "",
            "replacement_named": "",
        }
        if state == "absent":  # bye
            base.update({
                "players_listed": "", "qb_on_report": "", "dnp_count": "", "lp_count": "",
                "fp_count": "", "out_count": "", "questionable_count": "", "doubtful_count": "",
                "net_injury_count": "", "designations_printed": "",
                "flags": "F-TV-06",
                "source_url": "", "read_utc": "",
            })
        elif state == "no_injuries_reported":
            base.update({
                "players_listed": "0", "qb_on_report": "", "dnp_count": "0", "lp_count": "0",
                "fp_count": "0", "out_count": "0", "questionable_count": "0", "doubtful_count": "0",
                "net_injury_count": "0", "designations_printed": "YES_EXPLICIT",
                "flags": "F-TV-06",
                "source_url": SRC11 if week == 11 else SRC10,
                "read_utc": read_utc_default,
            })
        else:
            s = summarize(prows)
            desig_printed = "YES" if s["printed"] else "NO_NOT_PRINTED"
            base.update({
                "players_listed": str(s["listed"]),
                "qb_on_report": s["qb"],
                "dnp_count": str(s["dnp"]), "lp_count": str(s["lp"]), "fp_count": str(s["fp"]),
                "out_count": str(s["out"]) if s["printed"] else "",
                "questionable_count": str(s["q"]) if s["printed"] else "",
                "doubtful_count": str(s["d"]) if s["printed"] else "",
                "net_injury_count": str(s["net"]) if s["printed"] else "",
                "designations_printed": desig_printed,
                "flags": "F-TV-03" if not s["printed"] else "",
                "source_url": SRC11 if week == 11 else SRC10,
                "read_utc": read_utc_default,
            })
        out_rows.append(base)
    return out_rows


def build_delta(w10, w11):
    i10 = {r["club"]: r for r in w10}
    i11 = {r["club"]: r for r in w11}
    rows = []
    for club in sorted(set(i10) | set(i11)):
        a, b = i10.get(club), i11.get(club)

        def g(r, k):
            return "" if r is None else r.get(k, "")

        def n(v):
            return int(v) if v != "" else None

        def delta(ka, kb, note_ok=True):
            x, y = n(g(a, ka)), n(g(b, kb))
            if x is None or y is None:
                return ""
            return str(y - x)

        if a and b and a["status"] == "BYE":
            both = "BYE_W10"
        elif a and b and b["status"] == "BYE":
            both = "BYE_W11"
        elif a and b:
            both = "BOTH_PLAYED"
        else:
            both = "MISSING_SIDE"

        note = ""
        if both == "BYE_W10":
            note = "Week-10 bye: club not on reg10; delta not computable"
        elif both == "BYE_W11":
            note = "Week-11 bye: club not on reg11; delta not computable"
        elif both == "BOTH_PLAYED" and b.get("designations_printed") == "NO_NOT_PRINTED":
            note = "W11 designations not printed as of 2026-11-19 read; designation delta blank (F-TV-03)"

        flags = []
        if both.startswith("BYE"):
            flags.append("F-TV-06")
        if "F-TV-03" in (g(b, "flags") or ""):
            flags.append("F-TV-03")
        flags.append("F-TV-11")

        rows.append({
            "club": club,
            "club_name": CLUB_NAMES[club],
            "weeks_both": both,
            "listed_w10": g(a, "players_listed"),
            "listed_w11": g(b, "players_listed"),
            "delta_listed": delta("players_listed", "players_listed"),
            "dnp_w10": g(a, "dnp_count"),
            "dnp_w11": g(b, "dnp_count"),
            "delta_dnp": delta("dnp_count", "dnp_count"),
            "out_w10": g(a, "out_count"),
            "out_w11": g(b, "out_count"),
            "delta_out": delta("out_count", "out_count"),
            "net_w10": g(a, "net_injury_count"),
            "net_w11": g(b, "net_injury_count"),
            "delta_net": delta("net_injury_count", "net_injury_count"),
            "publication_state": "W10 final vs W11 Wednesday" if both == "BOTH_PLAYED" else "",
            "note": note,
            "flags": ";".join(dict.fromkeys(flags)),
            "source_url": f"{SRC10} ; {SRC11}",
            "read_utc": "2026-11-19T11:55Z-12:03Z ; 2026-11-19T11:46Z-11:52Z",
        })
    return rows


FIELDVIEW = [
    "club", "club_name", "week", "status", "opponent", "kickoff_printed", "network",
    "report_state", "players_listed", "qb_on_report", "dnp_count", "lp_count", "fp_count",
    "out_count", "questionable_count", "doubtful_count", "net_injury_count",
    "designations_printed", "starters_out", "replacement_named", "flags",
    "source_url", "read_utc",
]
FIELDDELTA = [
    "club", "club_name", "weeks_both", "listed_w10", "listed_w11", "delta_listed",
    "dnp_w10", "dnp_w11", "delta_dnp", "out_w10", "out_w11", "delta_out",
    "net_w10", "net_w11", "delta_net", "publication_state", "note", "flags",
    "source_url", "read_utc",
]


def write(name, rows, fields):
    with open(DATA / name, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def main():
    w11 = build_week(11, SRC11, "2026-11-19T11:46Z-11:52Z")
    w10 = build_week(10, SRC10, "2026-11-19T11:55Z-12:03Z")
    delta = build_delta(w10, w11)
    write("team_view_w11.csv", w11, FIELDVIEW)
    write("team_view_w10.csv", w10, FIELDVIEW)
    write("team_delta_w10_w11.csv", delta, FIELDDELTA)
    print(f"team_view_w11: {len(w11)} clubs")
    print(f"team_view_w10: {len(w10)} clubs")
    print(f"team_delta:    {len(delta)} clubs")


if __name__ == "__main__":
    main()

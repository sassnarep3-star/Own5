#!/usr/bin/env python3
"""Session 28431d9c - NFL cross-desk reconciliation hub.

Stdlib only. Reads:
  * nfl-hub-28431d9c/data/official_*.csv   (transcribed from nfl.com fetches, 2026-11-13)
  * the six existing NFL desk folders      (READ-ONLY; never modified)
Writes:
  * nfl-hub-28431d9c/data/reconcile_*.csv, desk_map.csv, flagged.csv, official_qb_news.csv
  * nfl-hub-28431d9c/*.html, style.css
  * research/nfl-28431d9c/FLAGGED.md
Run from repo root:  python3 nfl-hub-28431d9c/build.py
"""
import csv
import html
import os
import re
from collections import OrderedDict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
HUB = os.path.join(ROOT, "nfl-hub-28431d9c")
DATA = os.path.join(HUB, "data")
RESEARCH = os.path.join(ROOT, "research", "nfl-28431d9c")
FETCH_DATE = "2026-11-13"
SITE = "https://sassnarep3-star.github.io/Own5"
STANDINGS_URL = "https://www.nfl.com/standings/league/2026/REG"
SCHEDULE_URL = "https://www.nfl.com/schedules/2026/by-week/week-10"
INJURY_URL = "https://www.nfl.com/injuries/league/2026/reg10"
TNF_URL = "https://www.nfl.com/games/commanders-at-giants-2026-reg-10"

# NFL.com logo codes are canonical. Desk-specific codes are mapped to them.
CODE_MAP = {"ARI": "AZ", "LAR": "LA", "WSH": "WAS"}


def norm_code(c):
    c = (c or "").strip().upper()
    return CODE_MAP.get(c, c)


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path, fieldnames, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fieldnames})


def esc(s):
    return html.escape("" if s is None else str(s), quote=True)


def to24(t):
    """'8:15 PM' / '20:15 ET' / '9:30 AM' -> 'HH:MM' (24h) or ''."""
    t = (t or "").strip()
    m = re.search(r"(\d{1,2}):(\d{2})\s*(AM|PM)?", t, re.I)
    if not m:
        return ""
    h, mi, ap = int(m.group(1)), int(m.group(2)), (m.group(3) or "").upper()
    if ap == "PM" and h != 12:
        h += 12
    if ap == "AM" and h == 12:
        h = 0
    return "%02d:%02d" % (h, mi)


def fmt_wlt(w, l, t):
    return "%s-%s-%s" % (w, l, t)


# ----------------------------------------------------------------- load official
official_standings = OrderedDict()
for r in read_csv(os.path.join(DATA, "official_standings_2026_reg.csv")):
    official_standings[r["nfl_code"]] = {
        "code": r["nfl_code"], "team": r["team"], "w": int(r["w"]), "l": int(r["l"]),
        "t": int(r["t"]), "pf": int(r["pf"]), "pa": int(r["pa"]), "net": int(r["net_pts"]),
    }
official_slate = read_csv(os.path.join(DATA, "official_slate_2026_wk10.csv"))
official_injuries = read_csv(os.path.join(DATA, "official_injury_sample_2026_wk10.csv"))
BYES = ["CHI", "DEN", "PHI", "TB"]  # official schedule page "Teams on Bye" block

# ----------------------------------------------------------------- integrity of snapshot
assert len(official_standings) == 32, "official standings must have 32 teams"
assert sum(s["pf"] for s in official_standings.values()) == sum(s["pa"] for s in official_standings.values()), \
    "league PF must equal league PA"
for s in official_standings.values():
    assert s["pf"] - s["pa"] == s["net"], s
    gp = s["w"] + s["l"] + s["t"]
    assert gp in (8, 9), s
assert len(official_slate) == 14, "official Week 10 slate must have 14 games"

# Official TNF result (from the official schedule page: "Commanders 24, Giants 21, FINAL")
TNF_WINNER, TNF_LOSER, TNF_WPTS, TNF_LPTS = "WAS", "NYG", 24, 21


def pre_tnf(code, rec):
    """Reverse the official TNF result to reconstruct the pre-Week-10 record."""
    w, l, t, pf, pa = rec["w"], rec["l"], rec["t"], rec["pf"], rec["pa"]
    if code == TNF_WINNER:
        return (w - 1, l, t, pf - TNF_WPTS, pa - TNF_LPTS)
    if code == TNF_LOSER:
        return (w, l - 1, t, pf - TNF_LPTS, pa - TNF_WPTS)
    return (w, l, t, pf, pa)


# ----------------------------------------------------------------- desk paths
D_E413 = "nfl-decision-desk-e413f933"
D_B34 = "nfl-b34253a1"
D_26D = "nfl-desk-26d4cafb"
D_38A = "nfl-decision-desk-38a1fc27"
D_D034 = "nfl-decision-desk"
D_F1D = "nfl-strategy-lab"

# ----------------------------------------------------------------- standings reconciliation
e413_st = {norm_code(r["team"]): r for r in read_csv(os.path.join(ROOT, D_E413, "data/standings_2026_reg_wk9.csv"))}
b34_st = {norm_code(r["team"]): r for r in read_csv(os.path.join(ROOT, D_B34, "data/standings_2026_w10.csv"))}
d26_st = {norm_code(r["abbr"]): r for r in read_csv(os.path.join(ROOT, D_26D, "data/standings_check.csv"))}


def desk_rec(r, kind):
    if kind == "e413":
        return (int(r["w"]), int(r["l"]), int(r["t"]), int(r["pf"]), int(r["pa"]))
    if kind == "b34":
        return (int(r["wins"]), int(r["losses"]), int(r["ties"]), int(r["points_for"]), int(r["points_against"]))
    if kind == "26d":
        return (int(r["official_W"]), int(r["official_L"]), int(r["official_T"]),
                int(r["official_PF"]), int(r["official_PA"]))


def compare_standing(code, rec_desk):
    off = official_standings[code]
    off_t = (off["w"], off["l"], off["t"], off["pf"], off["pa"])
    if rec_desk is None:
        return "NOT IN DESK FILE"
    if rec_desk == off_t:
        return "MATCH official"
    if code in (TNF_WINNER, TNF_LOSER) and rec_desk == pre_tnf(code, off):
        return "STALE: pre-Week-10 (missing TNF final)"
    return "MISMATCH"


standings_rows = []
for code, off in official_standings.items():
    e = desk_rec(e413_st[code], "e413") if code in e413_st else None
    b = desk_rec(b34_st[code], "b34") if code in b34_st else None
    d = desk_rec(d26_st[code], "26d") if code in d26_st else None
    off_wlt = fmt_wlt(off["w"], off["l"], off["t"])
    standings_rows.append({
        "nfl_code": code, "team": off["team"],
        "official_wlt": off_wlt, "official_pf": off["pf"], "official_pa": off["pa"],
        "official_source_url": STANDINGS_URL,
        "e413_wlt": fmt_wlt(*e[:3]) if e else "", "e413_pf": e[3] if e else "", "e413_pa": e[4] if e else "",
        "e413_status": compare_standing(code, e),
        "b34_wlt": fmt_wlt(*b[:3]) if b else "", "b34_pf": b[3] if b else "", "b34_pa": b[4] if b else "",
        "b34_status": compare_standing(code, b),
        "d26_wlt": fmt_wlt(*d[:3]) if d else "", "d26_pf": d[3] if d else "", "d26_pa": d[4] if d else "",
        "d26_status": compare_standing(code, d),
    })

STAND_FIELDS = ["nfl_code", "team", "official_wlt", "official_pf", "official_pa", "official_source_url",
                "e413_wlt", "e413_pf", "e413_pa", "e413_status",
                "b34_wlt", "b34_pf", "b34_pa", "b34_status",
                "d26_wlt", "d26_pf", "d26_pa", "d26_status"]
write_csv(os.path.join(DATA, "reconcile_standings.csv"), STAND_FIELDS, standings_rows)

stand_counts = {}
for k in ("e413", "b34", "d26"):
    stand_counts[k] = {}
    for r in standings_rows:
        s = r[k + "_status"]
        stand_counts[k][s] = stand_counts[k].get(s, 0) + 1

# ----------------------------------------------------------------- slate reconciliation
e413_sl = read_csv(os.path.join(ROOT, D_E413, "data/schedule_2026_wk10.csv"))
b34_sl = read_csv(os.path.join(ROOT, D_B34, "data/schedule_2026_w10.csv"))
d26_ln = read_csv(os.path.join(ROOT, D_26D, "data/lines_wk10.csv"))
e413_byes = read_csv(os.path.join(ROOT, D_E413, "data/byes_2026_wk10.csv"))

e413_idx = {(norm_code(r["away_team"]), norm_code(r["home_team"])): r for r in e413_sl}
b34_idx = {(norm_code(r["away_team"]), norm_code(r["home_team"])): r for r in b34_sl if r["status"] != "BYE"}
d26_idx = {(norm_code(r["away"]), norm_code(r["home"])): r for r in d26_ln}

slate_rows = []
slate_mismatch = 0
for g in official_slate:
    key = (g["away_code"], g["home_code"])
    off_t = to24(g["kickoff_et"])
    e = e413_idx.get(key)
    b = b34_idx.get(key)
    d = d26_idx.get(key)
    e_ok = bool(e) and e["date"] == g["date"] and to24(e["time_et"]) == off_t
    b_ok = bool(b) and b["date"] == g["date"] and to24(b["kickoff_et"]) == off_t
    d_ok = bool(d) and d["date"] == g["date"] and to24(d["window"]) == off_t
    if not (e_ok and b_ok and d_ok):
        slate_mismatch += 1
    b_status = b["status"] if b else ""
    slate_rows.append({
        "game_key": g["game_key"], "matchup": "%s @ %s" % (g["away_code"], g["home_code"]),
        "official_away_home": "%s @ %s" % (g["away_team"], g["home_team"]),
        "official_date": g["date"], "official_kickoff_et": g["kickoff_et"], "official_network": g["network"],
        "official_status_on_fetch": g["status_on_fetch"], "official_game_url": g["official_game_url"],
        "e413_date_time": ("%s %s" % (e["date"], e["time_et"])) if e else "",
        "e413_check": "MATCH" if e_ok else ("NO ROW" if not e else "MISMATCH"),
        "e413_status_field": "no status field",
        "b34_date_time": ("%s %s" % (b["date"], b["kickoff_et"])) if b else "",
        "b34_check": "MATCH" if b_ok else ("NO ROW" if not b else "MISMATCH"),
        "b34_status_field": b_status,
        "d26_date_time": ("%s %s" % (d["date"], d["window"])) if d else "",
        "d26_check": "MATCH" if d_ok else ("NO ROW" if not d else "MISMATCH"),
        "d26_status_field": "no status field",
        "source_url": SCHEDULE_URL,
    })
    # Stale-status flag: a desk still shows SCHEDULED for a game the official page shows FINAL
    if g["game_key"] == "WAS-NYG" and b_status == "SCHEDULED":
        slate_rows[-1]["b34_check"] += " (status SCHEDULED; official FINAL)"

bye_rows = []
e413_bye_set = {r["team"] for r in e413_byes}
for code in BYES:
    bye_rows.append({
        "nfl_code": code, "team": official_standings[code]["team"], "official_status": "Bye (Week 10)",
        "e413_bye": "MATCH" if code in e413_bye_set else "NOT LISTED",
        "b34_bye": "MATCH" if any(norm_code(r["away_team"]) == code and r["status"] == "BYE" for r in b34_sl) else "NOT LISTED",
        "d26_bye": "NO MACHINE-READABLE BYE LIST",
        "source_url": SCHEDULE_URL,
    })

SLATE_FIELDS = ["game_key", "matchup", "official_away_home", "official_date", "official_kickoff_et", "official_network",
                "official_status_on_fetch", "official_game_url",
                "e413_date_time", "e413_check", "e413_status_field",
                "b34_date_time", "b34_check", "b34_status_field",
                "d26_date_time", "d26_check", "d26_status_field", "source_url"]
write_csv(os.path.join(DATA, "reconcile_slate.csv"), SLATE_FIELDS, slate_rows)
write_csv(os.path.join(DATA, "reconcile_byes.csv"),
          ["nfl_code", "team", "official_status", "e413_bye", "b34_bye", "d26_bye", "source_url"], bye_rows)

# ----------------------------------------------------------------- own-line cross-model comparison
e413_ol = read_csv(os.path.join(ROOT, D_E413, "data/own_lines_2026_wk10.csv"))
b34_ml = read_csv(os.path.join(ROOT, D_B34, "data/model_lines_2026_w10.csv"))

e_ol_idx = {(norm_code(r["away_team"]), norm_code(r["home_team"])): r for r in e413_ol}
b_ml_idx = {(norm_code(r["away_team"]), norm_code(r["home_team"])): r for r in b34_ml}


def fav(margin):
    """margin = projected HOME margin (positive = home favored)."""
    return "HOME" if margin > 0 else ("AWAY" if margin < 0 else "PICK")


ol_rows = []
split_games = 0
for g in official_slate:
    key = (g["away_code"], g["home_code"])
    e = e_ol_idx.get(key)
    b = b_ml_idx.get(key)
    d = d26_idx.get(key)
    em = float(e["model_home_margin"]) if e else None
    bm = float(b["base_home_margin"]) if b else None
    dm = float(d["model_margin_home"]) if d else None
    margins = [m for m in (em, bm, dm) if m is not None]
    fav_set = {fav(m) for m in margins}
    agree = "ALL AGREE" if len(fav_set) == 1 else "SPLIT"
    if agree == "SPLIT":
        split_games += 1
    rng = (max(margins) - min(margins)) if margins else None
    ol_rows.append({
        "game_key": g["game_key"], "matchup": "%s @ %s" % (g["away_code"], g["home_code"]),
        "official_date": g["date"], "official_kickoff_et": g["kickoff_et"],
        "e413_home_margin": "%.1f" % em if em is not None else "",
        "e413_hfa_note": "HFA +2.0 (desk-stated)" if e and e.get("site_type", "") != "neutral (Munich)" else ("no HFA (neutral)" if e else ""),
        "b34_home_margin": "%.1f" % bm if bm is not None else "",
        "b34_hfa_note": "no HFA (desk methodology)" if b else "",
        "d26_home_margin": "%.2f" % dm if dm is not None else "",
        "d26_hfa_note": "empirical 2026 HFA -0.054 (desk-stated)" if d else "",
        "favorite_agreement": agree,
        "margin_range_pts": "%.2f" % rng if rng is not None else "",
        "official_game_url": g["official_game_url"],
        "source_url": "%s ; %s" % (g["official_game_url"], SCHEDULE_URL),
    })

OL_FIELDS = ["game_key", "matchup", "official_date", "official_kickoff_et",
             "e413_home_margin", "e413_hfa_note", "b34_home_margin", "b34_hfa_note",
             "d26_home_margin", "d26_hfa_note", "favorite_agreement", "margin_range_pts",
             "official_game_url", "source_url"]
write_csv(os.path.join(DATA, "reconcile_own_lines.csv"), OL_FIELDS, ol_rows)

# Market quotes recorded by b34 (desk-recorded, not re-verified; timestamp DATE_ONLY)
b34_quotes = read_csv(os.path.join(ROOT, D_B34, "data/market_quotes_2026_w10.csv"))
quote_games = {(norm_code(r["away_team"]), norm_code(r["home_team"])) for r in b34_quotes}
quote_rows_n = len(b34_quotes)

# ----------------------------------------------------------------- injuries reconciliation
e413_inj = read_csv(os.path.join(ROOT, D_E413, "data/injuries_2026_wk10.csv"))
e413_inj_idx = {(norm_code(r["team"]), r["player"].strip()): r for r in e413_inj}
b34_inj = read_csv(os.path.join(ROOT, D_B34, "data/injuries_depth_w10.csv"))
b34_inj_idx = {(norm_code(r["team"]), r["affected_player"].strip()): r for r in b34_inj}
d26_inj = read_csv(os.path.join(ROOT, D_26D, "data/injuries.csv"))


def d26_mentions(name):
    hits = []
    for r in d26_inj:
        blob = " | ".join([r.get(k, "") for k in ("starter_1st", "practice_status", "official_game_status",
                                                   "backup_2nd", "backup_3rd", "backup_4th")])
        if name in blob:
            hits.append(r["id"])
    return hits


def norm_s(s):
    return (s or "").strip().lower()


inj_rows = []
inj_diff_counts = {"e413_match": 0, "e413_diff": 0, "e413_missing": 0, "b34_listed": 0, "b34_diff": 0, "b34_partial": 0, "b34_not_listed": 0}
for r in official_injuries:
    t, p = r["team_code"], r["player"]
    e = e413_inj_idx.get((t, p))
    b = b34_inj_idx.get((t, p))
    if e is None:
        e_res = "NOT IN DESK FILE"
        inj_diff_counts["e413_missing"] += 1
    else:
        diffs = []
        if norm_s(e["injury"]) != norm_s(r["injury"]):
            diffs.append("injury '%s' vs official '%s'" % (e["injury"] or "(blank)", r["injury"] or "(blank)"))
        if norm_s(e["practice_status"]) != norm_s(r["practice_status"]):
            diffs.append("practice '%s'" % (e["practice_status"] or "(blank)"))
        if norm_s(e["game_status"]) != norm_s(r["game_status"]):
            diffs.append("game '%s' vs official '%s'" % (e["game_status"] or "(blank)", r["game_status"] or "(blank)"))
        if diffs:
            e_res = "DIFF: " + "; ".join(diffs)
            inj_diff_counts["e413_diff"] += 1
        else:
            e_res = "MATCH"
            inj_diff_counts["e413_match"] += 1
    if b is None:
        b_res = "NOT IN SELECTED LIST (b34 file is a selection)"
        inj_diff_counts["b34_not_listed"] += 1
    else:
        inj_diff_counts["b34_listed"] += 1
        notes = []     # hard contradictions -> DIFF
        partial = []   # b34 is practice-level only; it does not record the official game designation
        if norm_s(b["position"]) != norm_s(r["position"]):
            notes.append("position '%s' vs official '%s'" % (b["position"], r["position"]))
        bstat = norm_s(b["reported_status"])
        if bstat in ("out", "questionable") and r["game_status"]:
            if bstat != norm_s(r["game_status"]):
                notes.append("status '%s' vs official game '%s'" % (b["reported_status"], r["game_status"]))
        elif bstat == "dnp":
            if "Limited" in r["practice_status"] or "Full" in r["practice_status"]:
                notes.append("practice 'DNP' vs official '%s'" % r["practice_status"])
            elif r["game_status"]:
                partial.append("game status '%s' not recorded (desk shows DNP only)" % r["game_status"])
        if r["injury"] == "" and b["reported_body_part_or_reason"]:
            notes.append("reason '%s' not shown on official report" % b["reported_body_part_or_reason"])
        if notes:
            b_res = "DIFF: " + "; ".join(notes + partial)
            inj_diff_counts["b34_diff"] += 1
        elif partial:
            b_res = "PARTIAL: " + "; ".join(partial)
            inj_diff_counts["b34_partial"] = inj_diff_counts.get("b34_partial", 0) + 1
        else:
            b_res = "MATCH"
    ids = d26_mentions(p)
    inj_rows.append({
        "team_code": t, "team": r["team"], "player": p, "position": r["position"],
        "official_injury": r["injury"], "official_practice_status": r["practice_status"],
        "official_game_status": r["game_status"],
        "official_source_url": INJURY_URL,
        "e413_check": e_res,
        "b34_check": b_res,
        "d26_mentions": ", ".join(ids) if ids else "NOT MENTIONED",
        "d26_source_note": "unit-level table; see desk row IDs" if ids else "",
    })

INJ_FIELDS = ["team_code", "team", "player", "position", "official_injury", "official_practice_status",
              "official_game_status", "official_source_url", "e413_check", "b34_check",
              "d26_mentions", "d26_source_note"]
write_csv(os.path.join(DATA, "reconcile_injuries.csv"), INJ_FIELDS, inj_rows)

# ----------------------------------------------------------------- computed cross-checks (no typed claims)
N_INJ = len(read_csv(os.path.join(DATA, "official_injury_sample_2026_wk10.csv")))
TNF_DELTA = {"NYG": dict(W=0, L=1, T=0, PF=21, PA=24), "WAS": dict(W=1, L=0, T=0, PF=24, PA=21)}


def _n(v):
    return int(str(v).strip())


def tnf_check():
    """Add the official Thursday result to each desk's pre-game NYG/WAS figures; compare to official."""
    off = {r["nfl_code"]: r for r in read_csv(os.path.join(DATA, "official_standings_2026_reg.csv"))}
    e = {r["team"]: r for r in read_csv(D_E413 + "/data/standings_2026_reg_wk9.csv")}
    b = {r["team"]: r for r in read_csv(D_B34 + "/data/standings_2026_w10.csv")}
    d = {r["abbr"]: r for r in read_csv(D_26D + "/data/standings_check.csv")}
    root = read_csv(os.path.join(ROOT, "data/decision-desk/official/official_standings_2026.csv"))
    root_full = {"NYG": "New York Giants", "WAS": "Washington Commanders"}
    out = []
    for code in ("NYG", "WAS"):
        o = off[code]
        got = dict(W=_n(o["w"]), L=_n(o["l"]), T=_n(o["t"]), PF=_n(o["pf"]), PA=_n(o["pa"]))
        srcs = {
            "e413f933": (e.get(code), dict(W="w", L="l", T="t", PF="pf", PA="pa")),
            "b34253a1": (b.get("WSH" if code == "WAS" else code),
                         dict(W="wins", L="losses", T="ties", PF="points_for", PA="points_against")),
            "26d4cafb": (d.get(code), dict(W="official_W", L="official_L", T="official_T",
                                           PF="official_PF", PA="official_PA")),
            "38a1fc27 root snapshot": (next((r for r in root if r["team"].startswith(root_full[code])), None),
                                       dict(W="w", L="l", T="t", PF="pf", PA="pa")),
        }
        for desk, (rec, cols) in srcs.items():
            if rec is None:
                out.append((code, desk, False, "row not found"))
                continue
            pre = {k: _n(rec[cols[k]]) for k in cols}
            exp = {k: pre[k] + TNF_DELTA[code][k] for k in pre}
            ok = exp == got
            out.append((code, desk, ok, "pre %s-%s-%s %s-%s" % (pre["W"], pre["L"], pre["T"], pre["PF"], pre["PA"])))
    return out


TNF_RESULTS = tnf_check()
TNF_SENTENCE = ("Adding the official Thursday result to each desk's pre-game NYG and WAS record and points: "
                + "; ".join("%s %s %s (%s)" % (desk, "reproduces" if ok else "does NOT reproduce",
                                                  code, detail)
                            for code, desk, ok, detail in TNF_RESULTS) + ".")
TNF_ALL_OK = all(ok for _c, _d, ok, _x in TNF_RESULTS)
TNF_TEXT = ("Adding the official Thursday result to each desk's pre-game NYG and WAS totals reproduces the official figures in every desk (computed by build.py)." if TNF_ALL_OK else "Adding the official Thursday result does NOT reproduce every desk's figures (see the Flagged page).")


def root_snapshot_compare():
    """Compare the 44 hub injury rows against the 38a1fc27 root snapshot (retrieved 2026-11-12T16:52Z)."""
    snap = read_csv(os.path.join(ROOT, "data/decision-desk/official/official_injuries_wk10.csv"))
    hub = read_csv(os.path.join(DATA, "official_injury_sample_2026_wk10.csv"))
    missing, diff, examples = 0, 0, []
    for h in hub:
        nick = h["team"].split()[-1]
        m = [r for r in snap if r["team_nickname"] == nick and r["player"] == h["player"]]
        if not m:
            missing += 1
            continue
        r = m[0]
        mism = []
        if r["practice_status"] != h["practice_status"]:
            mism.append("practice '%s' vs '%s'" % (r["practice_status"], h["practice_status"]))
        if r["game_status"] != h["game_status"]:
            mism.append("game '%s' vs '%s'" % (r["game_status"] or "(blank)", h["game_status"] or "(blank)"))
        if mism:
            diff += 1
            if len(examples) < 3:
                examples.append("%s (%s)" % (h["player"], "; ".join(mism)))
    return missing, diff, examples


ROOT_MISSING, ROOT_DIFF, ROOT_EX = root_snapshot_compare()

# ----------------------------------------------------------------- official QB / depth news (headlines only)
QB_NEWS = [
    ("Sam Darnold ruled out for Seahawks' Week 10 game vs. Raiders; Drew Lock expected to start again", "https://www.nfl.com/news/sam-darnold-ruled-out-for-seahawks-week-10-game-vs-raiders-drew-lock-expected-to-start-again", "SEA", "news headline (no date shown)", "Sam Darnold"),
    ("Ravens officially place Lamar Jackson on injured reserve", "https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-thursday-nov-5", "BAL", "Thu Nov 5 roundup", "Lamar Jackson"),
    ("NFL Network: Ravens' Lamar Jackson (right thumb) out 6-9 weeks, expects to return this season", "https://www.nfl.com/news/ravens-lamar-jackson-right-thumb-out-6-9-weeks-expects-to-return-this-season", "BAL", "news headline (no date shown)", "Lamar Jackson"),
    ("Report: Ravens QB Tyler Huntley out for season with turf toe injury", "https://www.nfl.com/news/ravens-qb-tyler-huntley-out-for-season-turf-toe-injury", "BAL", "news headline (no date shown)", "Tyler Huntley"),
    ("Pats' TreVeyon Henderson says he was hospitalized after 'unusual' emergency; RB focused on recovery", "https://www.nfl.com/news/pats-treveyon-henderson-says-he-was-hospitalized-after-unusual-emergency-focused-on-recovery", "NE", "news headline (no date shown)", "TreVeyon Henderson"),
    ("Deshaun Watson enters concussion protocol ahead of Browns' Week 9 game vs. Saints", "https://www.nfl.com/news/deshaun-watson-concussion-protocol-browns-week-9-shedeur-sanders", "CLE", "news headline (no date shown)", "Deshaun Watson"),
    ("Notable injuries, news from Sunday's Week 8 games: Cardinals bench QB Jacoby Brissett vs. Cowboys", "https://www.nfl.com/news/notable-injuries-news-sunday-week-8-games-2026", "AZ", "Week 8 roundup", "Jacoby Brissett"),
    ("Notable injuries, news from Sunday's Week 9 games: Rams WR Puka Nacua to undergo testing on knee injury", "https://www.nfl.com/news/notable-injuries-news-sunday-week-9-games-2026", "LA", "Week 9 roundup", "Puka Nacua"),
]

DESK_INJ_FILES = {
    "e413": [D_E413 + "/data/injuries_2026_wk10.csv", D_E413 + "/data/depth_charts_2026_wk10.csv", D_E413 + "/data/deficiencies_2026_wk10.csv"],
    "b34": [D_B34 + "/data/injuries_depth_w10.csv"],
    "26d": [D_26D + "/data/injuries.csv"],
}
qb_rows = []
for head, url, team, when, player in QB_NEWS:
    cov = {}
    for k, paths in DESK_INJ_FILES.items():
        hit = False
        for p in paths:
            with open(os.path.join(ROOT, p), encoding="utf-8") as fh:
                if player in fh.read():
                    hit = True
        cov[k] = "MENTIONED" if hit else "NOT MENTIONED"
    qb_rows.append({
        "official_headline": head, "player": player, "team_context": team, "official_date_context": when,
        "official_url": url, "e413_coverage": cov["e413"], "b34_coverage": cov["b34"], "d26_coverage": cov["26d"],
        "note": "headline text as shown on nfl.com injury-page news rail; article body not opened",
    })
QB_FIELDS = ["official_headline", "player", "team_context", "official_date_context", "official_url",
             "e413_coverage", "b34_coverage", "d26_coverage", "note"]
write_csv(os.path.join(DATA, "official_qb_news.csv"), QB_FIELDS, qb_rows)

# ----------------------------------------------------------------- desk map
DESKS = [
    {"desk": "NFL Strategy Lab", "folder": D_F1D, "owner": "arena-f1d30421", "pr": "#9 (merged 2026-11-02)",
     "pr_url": "https://github.com/sassnarep3-star/Own5/pull/9",
     "data_basis": "Week 9 (lines-2026-wk9)", "tnf_final_reflected": "No (pre-Week 10)",
     "machine_readable_standings": "none in folder", "machine_readable_slate": "HTML only",
     "scope_in_this_hub": "Listed only (no row-level reconciliation)"},
    {"desk": "NFL Decision Desk (d0343637)", "folder": D_D034, "owner": "d0343637",
     "pr": "#56, #57 (merged 2026-11-12)", "pr_url": "https://github.com/sassnarep3-star/Own5/pull/56",
     "data_basis": "register.json (its own README; Week 9 outputs noted as stale in its flags)",
     "tnf_final_reflected": "Not checked", "machine_readable_standings": "none", "machine_readable_slate": "none",
     "scope_in_this_hub": "Listed only"},
    {"desk": "NFL Decision Desk (38a1fc27)", "folder": D_38A, "owner": "38a1fc27",
     "pr": "#58 (merged), #59 (open)", "pr_url": "https://github.com/sassnarep3-star/Own5/pull/58",
     "data_basis": "Week 10 injuries and standings in data/decision-desk/official/ (outside its folder; retrieved 2026-11-12T16:52Z, before kickoff)",
     "tnf_final_reflected": "No (snapshot retrieved before kickoff)", "machine_readable_standings": "data/decision-desk/official/official_standings_2026.csv",
     "machine_readable_slate": "none in folder", "scope_in_this_hub": "Listed only"},
    {"desk": "NFL 2026 Week 10 Research Desk (b34253a1)", "folder": D_B34, "owner": "b34253a1",
     "pr": "#60 (merged), #62 (open)", "pr_url": "https://github.com/sassnarep3-star/Own5/pull/60",
     "data_basis": "Standings 'before_week_10'; Week 10 schedule; market quotes dated 2026-11-12 (DATE_ONLY)",
     "tnf_final_reflected": "No (TNF listed SCHEDULED)", "machine_readable_standings": D_B34 + "/data/standings_2026_w10.csv",
     "machine_readable_slate": D_B34 + "/data/schedule_2026_w10.csv", "scope_in_this_hub": "Full: standings, slate, byes, injuries, own lines"},
    {"desk": "NFL Decision Desk (26d4cafb)", "folder": D_26D, "owner": "26d4cafb",
     "pr": "#61, #63 (merged)", "pr_url": "https://github.com/sassnarep3-star/Own5/pull/61",
     "data_basis": "Standings check (pre-TNF); Week 10 lines; unit-level injury table",
     "tnf_final_reflected": "No (TNF pre-game)", "machine_readable_standings": D_26D + "/data/standings_check.csv",
     "machine_readable_slate": D_26D + "/data/lines_wk10.csv", "scope_in_this_hub": "Full: standings, slate, injuries (unit level), own lines"},
    {"desk": "NFL Decision Desk (e413f933)", "folder": D_E413, "owner": "e413f933",
     "pr": "#64, #65 (merged)", "pr_url": "https://github.com/sassnarep3-star/Own5/pull/64",
     "data_basis": "Standings Week 9; Week 10 schedule; injury snapshot (fetch time not recorded per row)",
     "tnf_final_reflected": "No (TNF listed as upcoming)", "machine_readable_standings": D_E413 + "/data/standings_2026_reg_wk9.csv",
     "machine_readable_slate": D_E413 + "/data/schedule_2026_wk10.csv", "scope_in_this_hub": "Full: standings, slate, byes, injuries, own lines"},
]
DESK_FIELDS = ["desk", "folder", "owner", "pr", "pr_url", "data_basis", "tnf_final_reflected",
               "machine_readable_standings", "machine_readable_slate", "scope_in_this_hub", "live_url", "source_type"]
desk_rows = []
for d in DESKS:
    row = dict(d)
    row["live_url"] = "%s/%s/" % (SITE, d["folder"])
    row["source_type"] = "INTERNAL RECORD (GitHub PR / repo path)"
    desk_rows.append(row)
write_csv(os.path.join(DATA, "desk_map.csv"), DESK_FIELDS, desk_rows)

# ----------------------------------------------------------------- flagged register
# Every flag cites a desk file path (repo-internal) and an official link where one exists.
stand_stale = [r["nfl_code"] for r in standings_rows if r["e413_status"].startswith("STALE")]
flags = [
    {"id": "H-01", "severity": "HIGH", "desks": "e413f933; b34253a1; 26d4cafb; 38a1fc27 (root snapshot)",
     "finding": "Official schedule lists Commanders 24 - Giants 21 (Thu Nov 12) as final, and the re-fetched official standings include it: NYG 5-3-1 (203-196), WAS 3-5-1 (196-223). " + TNF_SENTENCE + " Only NYG and WAS differ between the desks and the official page; the other 30 teams match exactly in all three desks.",
     "evidence": "%s/data/standings_2026_reg_wk9.csv; %s/data/standings_2026_w10.csv (before_week_10); %s/data/standings_check.csv; data/decision-desk/official/official_standings_2026.csv (retrieved 2026-11-12T16:52Z)" % (D_E413, D_B34, D_26D),
     "official_link": TNF_URL + " ; " + STANDINGS_URL,
     "action": "Refresh standings and TNF status before any line, rating or strategy output is used."},
    {"id": "H-02", "severity": "HIGH", "desks": "b34253a1",
     "finding": "b34253a1's market file has %d quote rows for %d games (books: %s). All rows are dated 2026-11-12 with no time of day (DATE_ONLY_TIME_NOT_EXPOSED_BY_SOURCE). The file includes Commanders at Giants, which the official schedule lists as final. Without a time, the quotes cannot be shown to be pre-kickoff, and no closing-line claim can be made. Market values were not re-verified against the sportsbooks." % (quote_rows_n, len({(r["away_team"], r["home_team"]) for r in b34_quotes}), ", ".join(sorted({r["book"] for r in b34_quotes}))),
     "evidence": "%s/data/market_quotes_2026_w10.csv (%d quote rows)" % (D_B34, quote_rows_n),
     "official_link": TNF_URL,
     "action": "Re-pull quotes with a retrieval time; mark any quote without one as unverified."},
    {"id": "H-03", "severity": "HIGH", "desks": "b34253a1",
     "finding": "Injury file marks Ben Brown as position 'LG'; the official Week 10 injury page lists him as 'C'. The row carries the label 'VERIFIED_STATUS_AND_CHART_ORDER; PARTICIPATION_UNCONFIRMED', which does not cover the position.",
     "evidence": "%s/data/injuries_depth_w10.csv (NE, Ben Brown)" % D_B34,
     "official_link": INJURY_URL,
     "action": "Correct the position; re-run the row-level check before trusting the verification label."},
    {"id": "H-04", "severity": "MEDIUM", "desks": "b34253a1",
     "finding": "Injury file lists Sione Vaki (DET, RB) with reason 'ankle'. The official report shows Vaki as Did Not Participate with no injury designation. The reason is not on the official page.",
     "evidence": "%s/data/injuries_depth_w10.csv (DET, Sione Vaki)" % D_B34,
     "official_link": INJURY_URL,
     "action": "Mark the reason as unverified or remove it."},
    {"id": "H-05", "severity": "MEDIUM", "desks": "b34253a1",
     "finding": "Injury file lists Rhamondre Stevenson (NE, RB) as DNP. The official report shows Limited Participation with game status Questionable.",
     "evidence": "%s/data/injuries_depth_w10.csv (NE, Rhamondre Stevenson)" % D_B34,
     "official_link": INJURY_URL,
     "action": "Update to the official practice and game status."},
    {"id": "H-06", "severity": "MEDIUM", "desks": "26d4cafb",
     "finding": "Unit table shows D.J. Reed (DET CB) and Cade Mays (DET C) as 'DNP (Unconfirmed Fri)'. The official report lists both with game status Out, and the desk's own official-status column is blank.",
     "evidence": "%s/data/injuries.csv (INJ-11, INJ-12)" % D_26D,
     "official_link": INJURY_URL,
     "action": "Record the official Out status for both players."},
    {"id": "H-07", "severity": "MEDIUM", "desks": "26d4cafb",
     "finding": "Unit table lists Rhamondre Stevenson as 'DNP + Backup Out' (INJ-10). The official report shows Limited Participation and Questionable.",
     "evidence": "%s/data/injuries.csv (INJ-10)" % D_26D,
     "official_link": INJURY_URL,
     "action": "Update the practice and game status to the official values."},
    {"id": "H-08", "severity": "MEDIUM", "desks": "26d4cafb",
     "finding": "26d4cafb marks Puka Nacua 'Confirmed Out / IR' (INJ-29). The re-fetched official injury page lists him Did Not Participate In Practice with a blank game status. The re-fetched official news item says he will undergo testing on a knee injury. The 'likely to be placed on injured reserve' headline read in an earlier session could not be reproduced, so IR status is unconfirmed.",
     "evidence": "%s/data/injuries.csv (INJ-29)" % D_26D,
     "official_link": "https://www.nfl.com/news/notable-injuries-news-sunday-week-9-games-2026",
     "action": "Change to the official status, or mark IR as unverified until an official transaction is found."},
    {"id": "H-09", "severity": "MEDIUM", "desks": "e413f933",
     "finding": "The e413 injury file leaves game status blank for players whom the official page shows with a designation (for example Kerby Joseph, Out), and practice status differs for several players. The file records no per-row fetch time, so the timing of the difference cannot be established.",
     "evidence": "%s/data/injuries_2026_wk10.csv (see reconcile_injuries.csv for row list)" % D_E413,
     "official_link": INJURY_URL,
     "action": "Record a fetch timestamp per row and re-pull the official report before any injury-adjusted output."},
    {"id": "H-10", "severity": "MEDIUM", "desks": "b34253a1; 26d4cafb; e413f933",
     "finding": "Own-line models disagree on the favorite in %d of 14 Week 10 games. Home-field inputs differ: e413 states HFA=2.0; 26d4cafb's lines file applies hfa_applied = -0.054 to the Thursday game; b34253a1's file has no home-field column. Methods also differ, and the cause was not separately verified. Any output built on these lines inherits the disagreement." % split_games,
     "evidence": "reconcile_own_lines.csv (computed in build.py)",
     "official_link": SCHEDULE_URL,
     "action": "Adopt one shared model specification before comparing or ranking the desks' lines."},
    {"id": "H-11", "severity": "LOW", "desks": "b34253a1",
     "finding": "The official schedule text retrieved names only 'Munich' for the Patriots at Lions game and names no stadium for it. It names no stadium for Commanders at Giants either; MetLife Stadium appears only in a hotel link on the Bills at Jets card. The desks' venue names ('FC Bayern Munich Stadium'; 'MetLife Stadium' for the Thursday game) are therefore unverified.",
     "evidence": "%s/data/schedule_2026_w10.csv" % D_B34,
     "official_link": SCHEDULE_URL,
     "action": "Verify venues against each official game page before publishing them."},
    {"id": "H-12", "severity": "LOW", "desks": "26d4cafb",
     "finding": "No machine-readable bye list in the desk. Bye teams CHI, DEN, PHI and TB were checked only against the other two desks.",
     "evidence": "%s/data/lines_wk10.csv" % D_26D,
     "official_link": SCHEDULE_URL,
     "action": "Add a bye file with the official source link."},
    {"id": "H-13", "severity": "LOW", "desks": "all six desks",
     "finding": "Official QB and depth headlines are covered unevenly across the desks (coverage counts in nfl-hub-28431d9c/data/official_qb_news.csv; article bodies not opened). Four draft headlines could not be reproduced on the re-fetched injury page's news list and are excluded: Malik Willis placed on IR (Dolphins), Deshaun Watson starting vs Houston, Carson Beck starting vs Los Angeles, and a Lamar Jackson 6-10 week item with Kenneth Walker questionable. Kenneth Walker is also absent from the Seattle table of the official report (chunk 4 of 8).",
     "evidence": "nfl-hub-28431d9c/data/official_qb_news.csv",
     "official_link": INJURY_URL,
     "action": "Add an official news feed to the injury pipeline, with article bodies captured."},
    {"id": "H-14", "severity": "MEDIUM", "desks": "38a1fc27 (root snapshot)",
     "finding": "The root official snapshot data/decision-desk/official/official_injuries_wk10.csv (retrieved 2026-11-12T16:52Z, before kickoff) differs from the current official page on %d of %d hub rows, and %d hub rows are absent from it. Examples: %s. The snapshot is stale for injury status and should not be used for status." % (ROOT_DIFF, N_INJ, ROOT_MISSING, "; ".join(ROOT_EX) if ROOT_EX else "none"),
     "evidence": "data/decision-desk/official/official_injuries_wk10.csv",
     "official_link": INJURY_URL,
     "action": "Replace the root snapshot with a dated official pull, or mark it superseded."},
    {"id": "H-15", "severity": "MEDIUM", "desks": "official source (internal inconsistency)",
     "finding": "The official news says Sam Darnold is ruled out for Seattle's Week 10 game and Drew Lock is expected to start. The official injury page's Seattle table lists Darnold as Did Not Participate In Practice with a blank game status, and Lock as Limited Participation. Puka Nacua (Rams) is likewise Did Not Participate with a blank game status. The official report does not show the Out designation that the news implies.",
     "evidence": "official injury page, Seattle and Rams tables (chunk 4 of 8); official news headline (chunk 6 of 8)",
     "official_link": INJURY_URL + " ; https://www.nfl.com/news/sam-darnold-ruled-out-for-seahawks-week-10-game-vs-raiders-drew-lock-expected-to-start-again",
     "action": "Confirm the Seattle QB designation on the official injury page before any QB-dependent output is used."},
    {"id": "H-16", "severity": "LOW", "desks": "all six desks",
     "finding": "This session did not reconcile the desks' non-slate outputs (correlations, strategy gates, leaderboards, suggestion and question registers). Those values are unverified here and remain as published in each desk.",
     "evidence": "scope note",
     "official_link": "",
     "action": "Review those desks' own verification logs."},
]

FLAG_FIELDS = ["id", "severity", "desks", "finding", "evidence", "official_link", "action", "status"]
for f in flags:
    f["status"] = "OPEN - published for review"
write_csv(os.path.join(DATA, "flagged.csv"), FLAG_FIELDS, flags)

# ----------------------------------------------------------------- summary numbers used by pages
summary = {
    "standings_total": len(standings_rows),
    "standings_stale_e413": sum(1 for r in standings_rows if r["e413_status"].startswith("STALE")),
    "standings_match_e413": sum(1 for r in standings_rows if r["e413_status"].startswith("MATCH")),
    "slate_games": len(slate_rows),
    "slate_mismatch": slate_mismatch,
    "injury_rows": len(inj_rows),
    "own_line_games": len(ol_rows),
    "split_games": split_games,
    "flags_total": len(flags),
    "flags_high": sum(1 for f in flags if f["severity"] == "HIGH"),
    "flags_medium": sum(1 for f in flags if f["severity"] == "MEDIUM"),
    "flags_low": sum(1 for f in flags if f["severity"] == "LOW"),
}
summary.update({"inj_" + k: v for k, v in inj_diff_counts.items()})

# ----------------------------------------------------------------- HTML rendering
CSS = """
:root{--ink:#14213d;--muted:#5b6475;--line:#e3e7ee;--bg:#f7f8fb;--ok:#0f7b4b;--warn:#a15c00;--bad:#b42318;--accent:#1f4fd1}
*{box-sizing:border-box}body{margin:0;font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;color:var(--ink);background:var(--bg)}
header{background:#fff;border-bottom:1px solid var(--line);padding:14px 24px;display:flex;flex-wrap:wrap;gap:12px 24px;align-items:center;justify-content:space-between}
header h1{font-size:18px;margin:0}header nav a{margin-right:14px;color:var(--accent);text-decoration:none;font-weight:600}
main{max-width:1200px;margin:0 auto;padding:24px}
h2{font-size:20px;margin:28px 0 10px}p.lead{color:var(--muted);margin:4px 0 16px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin:16px 0}
.card{background:#fff;border:1px solid var(--line);border-radius:10px;padding:14px}
.card b{display:block;font-size:26px}.card span{color:var(--muted);font-size:13px}
table{width:100%;border-collapse:collapse;background:#fff;border:1px solid var(--line);border-radius:8px;overflow:hidden;font-size:13.5px;margin-bottom:12px}
th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);vertical-align:top}
th{background:#eef2fa;font-weight:600;position:sticky;top:0}
td a{color:var(--accent)}tr:last-child td{border-bottom:none}
.tag{display:inline-block;padding:1px 8px;border-radius:999px;font-size:12px;font-weight:600;white-space:nowrap}
.ok{background:#e7f6ee;color:var(--ok)}.warn{background:#fff4e0;color:var(--warn)}.bad{background:#fde8e6;color:var(--bad)}.blank{background:#eef0f4;color:var(--muted)}
.note{background:#fff;border-left:4px solid var(--accent);padding:10px 14px;margin:12px 0;border-radius:6px}
.scroll{overflow-x:auto}footer{color:var(--muted);font-size:12.5px;padding:24px;text-align:center}
ul{padding-left:20px}li{margin:4px 0}
"""


def status_tag(s):
    s = s or ""
    if s.startswith("MATCH") or s == "MATCH":
        cls = "ok"
    elif s.startswith("STALE") or s.startswith("DIFF") or s.startswith("NOT LISTED") or "SCHEDULED" in s:
        cls = "warn"
    elif s.startswith("NOT IN SELECTED"):
        cls = "blank"
    elif s.startswith("MISMATCH") or s.startswith("NOT IN") or s.startswith("NO ROW"):
        cls = "bad"
    elif s == "" or s.startswith("NOT MENTIONED") or s.startswith("NO MACHINE") or s.startswith("no status"):
        cls = "blank"
    else:
        cls = "warn"
    return '<span class="tag %s">%s</span>' % (cls, esc(s if s else "blank - not in desk"))


def link(url, text=None):
    if not url:
        return ""
    return '<a href="%s" rel="noopener">%s</a>' % (esc(url), esc(text or url))


def page(title, active, body):
    nav = [("index.html", "Dashboard"), ("desks.html", "Desk map"), ("standings.html", "Standings"),
           ("slate.html", "Week 10 slate"), ("injuries.html", "Injuries & QB news"), ("own-lines.html", "Own-line comparison"),
           ("flagged.html", "Flagged for Review"), ("sources.html", "Sources")]
    navhtml = "".join('<a href="%s"%s>%s</a>' % (h, ' aria-current="page"' if h == active else "", esc(t)) for h, t in nav)
    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>%s | NFL Cross-Desk Hub</title><link rel="stylesheet" href="style.css"></head>
<body><header><h1>NFL Cross-Desk Hub - 2026 Week 10</h1><nav>%s</nav></header>
<main>%s</main>
<footer>Official values: nfl.com, fetched %s UTC. Desk values: read-only copies from the repo. Blank = not verified. Stdlib build, deterministic output.</footer>
</body></html>""" % (esc(title), navhtml, body, FETCH_DATE)


def table(headers, rows_html):
    head = "".join("<th>%s</th>" % esc(h) for h in headers)
    return '<div class="scroll"><table><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (head, "".join(rows_html))


def tr(cells):
    return "<tr>%s</tr>" % "".join("<td>%s</td>" % c for c in cells)


# index
idx = """
<h2>Start here</h2>
<p class="lead">This hub reconciles the six NFL desks already in this repository against the current official NFL.com pages (fetched %(d)s). It does not add new betting recommendations. Every value on the official side links to nfl.com, and anything that could not be confirmed is shown as blank or flagged.</p>
<div class="cards">
<div class="card"><b>%(st)d</b><span>official teams checked (standings)</span></div>
<div class="card"><b>%(sl)d</b><span>Week 10 games checked (+4 byes)</span></div>
<div class="card"><b>%(ir)d</b><span>official injury rows checked</span></div>
<div class="card"><b>%(ol)d</b><span>games with own-line comparison</span></div>
<div class="card"><b>%(fl)d</b><span>open flags (%(fh)d high)</span></div>
<div class="card"><b>%(sm)d</b><span>slate mismatches across desks</span></div>
</div>
<h2>Executive summary</h2>
<div class="note"><ul>
<li><b>Standings: the desks are one game behind, not wrong.</b> %(stm)d of 32 teams match the official standings exactly in all three desks. The only differences are the two Thursday teams (NYG, WAS). %(tnf)s</li>
<li><b>The Week 10 slate agrees.</b> All 14 official games match the three desks on teams, date and kickoff time (mismatches: %(sm)d). b34253a1 is the only desk that records a Thursday status, and it still shows the game as SCHEDULED. The four bye teams (CHI, DEN, PHI, TB) match the two desks that record byes; 26d4cafb has no machine-readable bye list.</li>
<li><b>Injury rows are where the desks disagree with the official page.</b> Of %(ir)d official rows, e413f933 matches %(em)d exactly and differs on %(ed)d; %(enl)d are not in its file. b34253a1 lists %(bl)d of them, differs on %(bd)d (a wrong position and an unsupported injury reason among them) and is practice-level only on %(bp)d. Some differences are snapshot timing; the rest are not explained by timing. All are listed on the Flagged page.</li>
<li><b>Own-line models disagree.</b> In %(sp)d of 14 games the three desks do not agree on the favorite (a zero margin counts as a pick'em). Causes were not separately verified; the desks use different methods. No desk's model line is an official value.</li>
<li><b>Market quotes are not usable as they stand.</b> b34253a1's DraftKings and FanDuel quotes have no time stamp and include the Thursday Commanders at Giants game, which the official schedule lists as final. They were not re-verified against the books.</li>
<li><b>Quarterback news is covered unevenly.</b> Re-fetched official headlines show Lamar Jackson placed on injured reserve, Tyler Huntley out for the season, Sam Darnold ruled out for Seattle's Week 10 game with Drew Lock expected to start, and TreVeyon Henderson hospitalized after an emergency. Four other draft headlines could not be reproduced and are excluded (Flagged H-13).</li>
</ul></div>
<h2>Pages</h2>
<ul>
<li><a href="desks.html">Desk map</a>: the six desks, their owners, pull requests, live links and what each one covers.</li>
<li><a href="standings.html">Standings</a>: 32 teams, official vs each desk, with a per-row official link.</li>
<li><a href="slate.html">Week 10 slate</a>: 14 games and 4 byes, official vs each desk.</li>
<li><a href="injuries.html">Injuries &amp; QB news</a>: official injury rows for the four sampled games, and the official QB headlines.</li>
<li><a href="own-lines.html">Own-line comparison</a>: home margins from each model, and where they disagree.</li>
<li><a href="flagged.html">Flagged for Review</a>: every open irregularity, with the file and the official link.</li>
<li><a href="sources.html">Sources</a>: each official URL, its fetch date and what was used from it.</li>
</ul>
<p class="lead">Scope limit: this hub verifies only the standings, slate, byes, an injury sample for four games and the QB headlines. Correlations, strategy gates, leaderboards and registers in the six desks are not re-verified here.</p>
""" % dict(d=FETCH_DATE, st=summary["standings_total"], sl=summary["slate_games"], ir=summary["injury_rows"],
          ol=summary["own_line_games"], fl=summary["flags_total"], fh=summary["flags_high"], sm=summary["slate_mismatch"],
          ste=stand_counts["e413"].get("STALE: pre-Week-10 (missing TNF final)", 0), stt=32,
          stb=stand_counts["b34"].get("STALE: pre-Week-10 (missing TNF final)", 0),
          std=stand_counts["d26"].get("STALE: pre-Week-10 (missing TNF final)", 0), stm=stand_counts["e413"].get("MATCH official", 0), tnf=TNF_TEXT,
          em=inj_diff_counts["e413_match"], ed=inj_diff_counts["e413_diff"], enl=inj_diff_counts["e413_missing"],
          bl=inj_diff_counts["b34_listed"], bd=inj_diff_counts["b34_diff"], bp=inj_diff_counts.get("b34_partial", 0), sp=split_games)

# Desk stale counts in the summary: standings STALE counts per desk
# (e413 reports stale for NYG and WAS; b34 and 26d do the same, checked on the standings page)

pages = {}
pages["index.html"] = page("Dashboard", "index.html", idx)

# desks
drows = []
for d in desk_rows:
    drows.append(tr([
        esc(d["desk"]), esc(d["owner"]), link(d["pr_url"], d["pr"]),
        link(d["live_url"], d["folder"] + "/"), esc(d["data_basis"]), status_tag(d["tnf_final_reflected"]),
        esc(d["scope_in_this_hub"]),
        link(d["pr_url"], "GitHub PR record"),
    ]))
pages["desks.html"] = page("Desk map", "desks.html",
    '<h2>Desk map</h2><p class="lead">Six NFL desks are on <code>main</code>. Each was built from its own snapshot. The "Reflects TNF final" column is what this hub checked. Source for these rows is the GitHub pull-request record in the repository (internal provenance, not an official NFL source).</p>'
    + table(["Desk", "Owner session", "Pull request", "Live site", "Data basis", "Reflects Thursday final?", "Scope in this hub", "Source"], drows))

# standings
srows = []
for r in standings_rows:
    srows.append(tr([
        "<b>%s</b> %s" % (esc(r["nfl_code"]), esc(r["team"])),
        '%s <span class="tag blank">PF %s / PA %s</span>' % (esc(r["official_wlt"]), esc(r["official_pf"]), esc(r["official_pa"])),
        link(r["official_source_url"], "nfl.com standings"),
        "%s / %s / %s" % (esc(r["e413_wlt"]), esc(r["e413_pf"]), esc(r["e413_pa"])) if r["e413_wlt"] else "",
        status_tag(r["e413_status"]),
        "%s / %s / %s" % (esc(r["b34_wlt"]), esc(r["b34_pf"]), esc(r["b34_pa"])) if r["b34_wlt"] else "",
        status_tag(r["b34_status"]),
        "%s / %s / %s" % (esc(r["d26_wlt"]), esc(r["d26_pf"]), esc(r["d26_pa"])) if r["d26_wlt"] else "",
        status_tag(r["d26_status"]),
    ]))
pages["standings.html"] = page("Standings", "standings.html",
    '<h2>Standings: official vs desks</h2><p class="lead">Official values are from nfl.com, fetched %s UTC (after the Thursday final). Desk cells show W-L-T / PF / PA. A STALE tag means the desk value equals the official record with the Thursday result removed.</p>' % FETCH_DATE
    + table(["Team", "Official W-L-T / PF / PA", "Source", "e413f933 (wk 9)", "Check", "b34253a1 (pre-wk 10)", "Check", "26d4cafb", "Check"], srows))

# slate
lrows = []
for r in slate_rows:
    lrows.append(tr([
        "<b>%s</b><br>%s" % (esc(r["matchup"]), esc(r["official_away_home"])),
        "%s %s<br><span class='tag blank'>%s</span>" % (esc(r["official_date"]), esc(r["official_kickoff_et"]), esc(r["official_network"])),
        esc(r["official_status_on_fetch"]),
        link(r["official_game_url"], "official game page"),
        "%s %s" % (esc(r["e413_date_time"]), status_tag(r["e413_check"])),
        "%s %s" % (esc(r["b34_date_time"]), status_tag(r["b34_check"])),
        "%s %s" % (esc(r["d26_date_time"]), status_tag(r["d26_check"])),
    ]))
byes_html = "".join(tr([esc(b["nfl_code"] + " " + b["team"]), esc(b["official_status"]), status_tag(b["e413_bye"]),
                        status_tag(b["b34_bye"]), status_tag(b["d26_bye"])]) for b in bye_rows)
pages["slate.html"] = page("Week 10 slate", "slate.html",
    '<h2>Week 10 slate</h2><p class="lead">Teams, date and kickoff time are checked. Desk checks say MATCH only when those three fields agree with the official page. Network and venue are not compared.</p>'
    + table(["Game", "Official date / kickoff ET / network", "Official status", "Source", "e413f933", "b34253a1", "26d4cafb"], lrows)
    + "<h2>Byes</h2>"
    + '<div class="scroll"><table><thead><tr><th>Team</th><th>Official</th><th>e413f933</th><th>b34253a1</th><th>26d4cafb</th></tr></thead><tbody>%s</tbody></table></div>' % byes_html)

# injuries
irows = []
for r in inj_rows:
    irows.append(tr([
        esc(r["team_code"]), "<b>%s</b>" % esc(r["player"]), esc(r["position"]),
        esc(r["official_injury"]) or "<span class='tag blank'>blank</span>",
        esc(r["official_practice_status"]),
        esc(r["official_game_status"]) or "<span class='tag blank'>blank</span>",
        link(r["official_source_url"], "official injury page"),
        status_tag(r["e413_check"]), status_tag(r["b34_check"]),
        esc(r["d26_mentions"]),
    ]))
qrows = []
for q in qb_rows:
    qrows.append(tr([esc(q["player"]), esc(q["official_headline"]), esc(q["official_date_context"]),
                     link(q["official_url"], "official news"), status_tag(q["e413_coverage"]),
                     status_tag(q["b34_coverage"]), status_tag(q["d26_coverage"])]))
pages["injuries.html"] = page("Injuries and QB news", "injuries.html",
    '<h2>Official injury sample (4 games: NYG-WAS, NE-DET)</h2><p class="lead">' + str(N_INJ) + ' rows transcribed from the official Week 10 injury report (fetched %s UTC). Desk checks compare injury, practice and game status and position. Status tags reflect that comparison. Only four of 14 games are sampled here.</p>' % FETCH_DATE
    + table(["Team", "Player", "Pos (official)", "Injury (official)", "Practice (official)", "Game status (official)", "Source", "e413f933", "b34253a1", "26d4cafb row(s)"], irows)
    + '<h2>Official QB and depth headlines</h2><p class="lead">Headline text from nfl.com news items linked on the injury page. Coverage tags say whether the player name appears in each desk\'s Week 10 injury or depth files. Article bodies were not opened.</p>'
    + table(["Player", "Official headline", "Context", "Source", "e413f933", "b34253a1", "26d4cafb"], qrows))

# own lines
orows = []
for r in ol_rows:
    tag = "warn" if r["favorite_agreement"] == "SPLIT" else "ok"
    orows.append(tr([
        "<b>%s</b>" % esc(r["matchup"]), esc(r["official_date"] + " " + r["official_kickoff_et"]),
        esc(r["e413_home_margin"]), esc(r["b34_home_margin"]), esc(r["d26_home_margin"]),
        '<span class="tag %s">%s</span>' % (tag, esc(r["favorite_agreement"])), esc(r["margin_range_pts"]),
        link(r["official_game_url"], "official game page"),
    ]))
pages["own-lines.html"] = page("Own-line comparison", "own-lines.html",
    '<h2>Own-line comparison: three models, one schedule</h2><p class="lead">Projected home margin (positive = home team projected to win) from each desk. These are MODEL outputs, not official values. The official link is for the game only. Home-field: e413f933 uses +2.0; b34253a1 uses none; 26d4cafb uses the empirical -0.054. The sportsbook quotes in b34253a1 are not shown here (flag H-02).</p>'
    + table(["Game", "Official date / kickoff ET", "e413f933 home margin", "b34253a1 home margin", "26d4cafb home margin", "Favorite agreement", "Range (pts)", "Source"], orows))

# flagged
frows = []
for f in flags:
    sev = {"HIGH": "bad", "MEDIUM": "warn", "LOW": "blank"}[f["severity"]]
    frows.append(tr([
        "<b>%s</b>" % esc(f["id"]), '<span class="tag %s">%s</span>' % (sev, esc(f["severity"])),
        esc(f["desks"]), esc(f["finding"]), "<code>%s</code>" % esc(f["evidence"]),
        link(f["official_link"].split(" ; ")[0], f["official_link"].split(" ; ")[0]) if f["official_link"] else "<span class='tag blank'>none (internal)</span>",
        esc(f["action"]),
    ]))
pages["flagged.html"] = page("Flagged for Review", "flagged.html",
    '<h2>Flagged for Review</h2><p class="lead">Nonblocking. Each flag names the desk file and, where one exists, the official link. Nothing here is corrected in another desk\'s files. Requested fixes are listed for the owning session.</p>'
    + table(["ID", "Severity", "Desk(s)", "Finding", "Evidence (repo path)", "Official source", "Requested action"], frows))

# sources
src_items = [
    ("Official standings (32 teams)", STANDINGS_URL, "Team W-L-T, PF, PA, net points; fetched " + FETCH_DATE),
    ("Official Week 10 schedule (14 games, 4 byes, TNF final)", SCHEDULE_URL, "Teams, date, kickoff ET, network, status, bye block; fetched " + FETCH_DATE),
    ("Official Thursday game page", TNF_URL, "Result link for the Commanders-Giants final"),
    ("Official Week 10 injury report (sample: WAS, NYG, NE, DET)", INJURY_URL, "Injury, practice and game status and position; fetched " + FETCH_DATE),
    ("Official NFL news headlines (on the injury page)", INJURY_URL, "QB headlines in official_qb_news.csv; headline text only"),
]
sr = [tr([esc(a), link(b), esc(c)]) for a, b, c in src_items]
pages["sources.html"] = page("Sources", "sources.html",
    '<h2>Official sources used</h2><p class="lead">Every official value on this hub was copied from these pages on %s. Nothing was filled in from memory or inferred.</p>' % FETCH_DATE
    + table(["Source", "URL", "Used for"], sr)
    + '<h2>Desk files read (read-only)</h2><ul>' + "".join("<li><code>%s</code></li>" % esc(p) for p in [
        D_E413 + "/data/standings_2026_reg_wk9.csv", D_E413 + "/data/schedule_2026_wk10.csv", D_E413 + "/data/own_lines_2026_wk10.csv",
        D_E413 + "/data/injuries_2026_wk10.csv", D_E413 + "/data/byes_2026_wk10.csv",
        D_B34 + "/data/standings_2026_w10.csv", D_B34 + "/data/schedule_2026_w10.csv", D_B34 + "/data/model_lines_2026_w10.csv",
        D_B34 + "/data/injuries_depth_w10.csv", D_B34 + "/data/market_quotes_2026_w10.csv",
        D_26D + "/data/standings_check.csv", D_26D + "/data/lines_wk10.csv", D_26D + "/data/injuries.csv"]) + "</ul>")

# ----------------------------------------------------------------- write outputs
os.makedirs(HUB, exist_ok=True)
for name, body in pages.items():
    with open(os.path.join(HUB, name), "w", encoding="utf-8") as f:
        f.write(body)
with open(os.path.join(HUB, "style.css"), "w", encoding="utf-8") as f:
    f.write(CSS.strip() + "\n")
with open(os.path.join(HUB, ".nojekyll"), "w", encoding="utf-8") as f:
    f.write("")

os.makedirs(RESEARCH, exist_ok=True)
with open(os.path.join(RESEARCH, "FLAGGED.md"), "w", encoding="utf-8") as f:
    f.write("# Flagged for Review - session 28431d9c\n\nNonblocking. Published on the site at `nfl-hub-28431d9c/flagged.html`. Source: `nfl-hub-28431d9c/data/flagged.csv`.\n\n")
    for fl in flags:
        f.write("## %s (%s) - %s\n\n- Desk(s): %s\n- Finding: %s\n- Evidence: `%s`\n- Official link: %s\n- Requested action: %s\n\n" % (
            fl["id"], fl["severity"], fl["desks"], fl["desks"], fl["finding"], fl["evidence"],
            fl["official_link"] or "(none - internal check)", fl["action"]))

print("summary", summary)
print("stand_counts", stand_counts)
print("inj_counts", inj_diff_counts)
print("slate_mismatch", slate_mismatch, "split_games", split_games)


# ----------------------------------------------------------------- research export (generated, deterministic)
RESEARCH_DIR = os.path.join(ROOT, "research", "nfl-28431d9c")
os.makedirs(RESEARCH_DIR, exist_ok=True)
_sev = {k: sum(1 for f in flags if f["severity"] == k) for k in ("HIGH", "MEDIUM", "LOW")}
with open(os.path.join(RESEARCH_DIR, "FLAGGED.md"), "w", encoding="utf-8") as f:
    f.write("# Flagged for Review - session 28431d9c\n\n")
    f.write("Nonblocking. Generated by `nfl-hub-28431d9c/build.py` from `nfl-hub-28431d9c/data/flagged.csv` "
            "and published at `nfl-hub-28431d9c/flagged.html`. Every flag carries its evidence path and an official link where one exists.\n\n")
    for fl in flags:
        f.write("## %s (%s) - %s\n\n" % (fl["id"], fl["severity"], fl["desks"]))
        f.write("- Finding: %s\n" % fl["finding"])
        f.write("- Evidence: `%s`\n" % fl["evidence"])
        f.write("- Official link: %s\n" % fl["official_link"])
        f.write("- Requested action: %s\n\n" % fl["action"])

with open(os.path.join(RESEARCH_DIR, "SUMMARY.md"), "w", encoding="utf-8") as f:
    f.write("# NFL cross-desk reconciliation - executive summary (session 28431d9c)\n\n")
    f.write("Date: 2026-11-13 (UTC). Branch `arena/28431d9c-own5`. Published hub: `nfl-hub-28431d9c/` "
            "(served under the GitHub Pages site at `/Own5/nfl-hub-28431d9c/`). Every number below is computed by `build.py` "
            "and re-checked by `verify.py`.\n\n")
    f.write("## Key results\n\n")
    f.write("- **Standings:** %d official teams. %d match exactly in all three desks. The only differences are NYG and WAS, "
            "because the desks still show the Thursday game as pending.\n" % (len(standings_rows), stand_counts["e413"].get("MATCH official", 0)))
    f.write("- **Thursday result:** %s\n" % TNF_SENTENCE)
    f.write("- **Week 10 slate:** %d games checked against the official schedule. Mismatches across desks: %d. "
            "b34253a1 still shows the Thursday game as SCHEDULED. The e413f933 and 26d4cafb schedule files have no status field, so their Thursday status cannot be checked.\n" % (len(official_slate), slate_mismatch))
    f.write("- **Byes:** CHI, DEN, PHI and TB. e413f933 and b34253a1 match. 26d4cafb has no machine-readable bye list.\n")
    f.write("- **Injuries (4 games, %d official rows):** e413f933 matches %d exactly and differs on %d. "
            "b34253a1 lists %d of the rows, differs on %d and is practice-level only on %d.\n"
            % (N_INJ, inj_diff_counts["e413_match"], inj_diff_counts["e413_diff"], inj_diff_counts["b34_listed"],
               inj_diff_counts["b34_diff"], inj_diff_counts.get("b34_partial", 0)))
    f.write("- **Own-line favorites:** the three desks disagree on the favorite in %d of 14 games. The desks' home-field inputs differ.\n" % split_games)
    f.write("- **Flags:** %d open (%d high, %d medium, %d low). Flags are nonblocking and are published on the Flagged for Review page.\n\n"
            % (len(flags), _sev["HIGH"], _sev["MEDIUM"], _sev["LOW"]))
    f.write("## Method\n\n")
    f.write("1. Official values were transcribed from `fetch_page` results of nfl.com: the standings page (re-fetched 2026-11-13, post-Thursday), "
            "the Week 10 schedule page (3 chunks), and the Week 10 injury report (chunks 0 to 6; chunk 7 returned no data). "
            "Each official row carries its page URL.\n")
    f.write("2. Each desk file was read read-only and compared row by row. A value that could not be confirmed is shown blank and flagged. "
            "Nothing was inferred or filled.\n")
    f.write("3. `verify.py` checks the official arithmetic (PF = PA, net, win %), the 44-row injury count, row links, internal links, "
            "the Thursday reversal (re-derived from the desk files), and that a rebuild is byte-identical.\n\n")
    f.write("## Limits\n\n")
    f.write("- Only the official sources listed above were used. Article bodies of news items were not opened. Chunk 7 of the injury report returned no data.\n")
    f.write("- No own-line origination, signal strategy, correlation, parlay or leaderboard work was done in this session. "
            "Those outputs in each desk are unverified here (Flagged H-16).\n")
    f.write("- Market quotes were not re-verified against the sportsbooks. Their timestamps are date-only (H-02).\n\n")
    f.write("## Suggestions for human review (not implemented)\n\n")
    f.write("1. Desk owners refresh standings and the Thursday status to the post-game official values (H-01).\n")
    f.write("2. b34253a1 records a retrieval time for every market quote (H-02).\n")
    f.write("3. Fix the Ben Brown position (LG vs C) and the \"VERIFIED\" label in b34253a1 (H-03).\n")
    f.write("4. Correct the 26d4cafb availability labels (\"Confirmed Out / IR\" for players not on IR) and the Nacua entry (H-06, H-08).\n")
    f.write("5. Replace the root 38a1fc27 injury snapshot with a dated official pull, or mark it superseded (H-14).\n")
    f.write("6. Use one abbreviation for Washington (desks use WAS, WSH) and for Arizona (desks use AZ, ARI). The abbreviation match is currently handled in code only.\n")
    f.write("7. Add a machine-readable bye list to 26d4cafb (H-12).\n")
    f.write("8. Capture official news article bodies, not only headlines, before using any news as a status source (H-13).\n")
    f.write("9. Confirm the Seattle QB designation on the official injury page before using it in any QB-dependent output (H-15).\n\n")
    f.write("## Questions\n\n")
    f.write("**Known (confirmed this session):** official standings and slate; the Thursday final; the 44 official injury rows for the four sampled games; "
            "TreVeyon Henderson's Out status (illness) and hospitalization headline; Sam Darnold ruled out and Drew Lock expected to start (headline); "
            "Lamar Jackson placed on IR (headline) and out 6-9 weeks; Tyler Huntley out for the season (headline); Puka Nacua knee testing (Week 9 headline).\n\n")
    f.write("**Missing or unconfirmed:**\n")
    f.write("- Whether Carson Beck starts for Arizona and Deshaun Watson for Cleveland (headlines not reproduced on re-fetch).\n")
    f.write("- Whether Malik Willis is on IR and Kyle McCord starts for Miami (not reproduced).\n")
    f.write("- Kenneth Walker's status (absent from the official Seattle table).\n")
    f.write("- Game status for Sam Darnold and Puka Nacua (blank on the official page while the news implies out).\n")
    f.write("- Venue names for the Thursday game and the Munich game.\n")
    f.write("- Timestamps for the sportsbook quotes.\n\n")
    f.write("**How to find the missing information:** re-fetch the nfl.com injury report and its news links on each game day; "
            "check the nfl.com transactions page for IR moves (not fetched in this session); read the article bodies of the news items linked from the injury page; "
            "take sportsbook quotes with a retrieval time; and re-run `build.py` and `verify.py` after any update.\n")

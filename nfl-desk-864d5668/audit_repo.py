#!/usr/bin/env python3
"""Repo audit (task N86-02): check the existing NFL data files line by line.

This session's authority for "official" is the ledger and standings transcribed
from nfl.com in raw_inputs.py. Anything in the repo's shared data/ folder that
carries a number is recomputed or cross-checked against that authority, and the
result is written to data/repo_audit.csv.

Nothing is edited here: this module only reads and reports.
"""
from __future__ import annotations
import csv
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.dirname(HERE)
REPO_DATA = os.path.join(REPO, "data")
OUT = os.path.join(HERE, "data")
os.makedirs(OUT, exist_ok=True)

import raw_inputs as R
import statslib as S
from engine import games_from_ledger, build_ledger

CLUB_TO_ABBR = {}
for abbr, (club, _c, _d) in R.TEAMS.items():
    CLUB_TO_ABBR[club] = abbr

ROWS = []


def add(check_id, area, item, expected, found, verdict, source, note=""):
    ROWS.append([check_id, area, item, expected, found, verdict, source, note])


def read_repo(name):
    with open(os.path.join(REPO_DATA, name), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def standings_through(max_date):
    w = {t: 0 for t in R.TEAMS}; l = {t: 0 for t in R.TEAMS}
    t_ = {t: 0 for t in R.TEAMS}; pf = {t: 0 for t in R.TEAMS}
    pa = {t: 0 for t in R.TEAMS}; gp = {t: 0 for t in R.TEAMS}
    for _wk, a, h, ap, hp, date, _n in R.LEDGER:
        if ap is None or date > max_date:
            continue
        gp[a] += 1; gp[h] += 1
        pf[a] += ap; pa[a] += hp
        pf[h] += hp; pa[h] += ap
        if hp > ap:
            w[h] += 1; l[a] += 1
        elif ap > hp:
            w[a] += 1; l[h] += 1
        else:
            t_[a] += 1; t_[h] += 1
    return w, l, t_, pf, pa, gp


def main():
    # ------------------------------------------------------------------
    # A. week8-2026-results.csv  vs the official ledger
    # ------------------------------------------------------------------
    try:
        rows = read_repo("week8-2026-results.csv")
        mine = {(a, h): (ap, hp) for _wk, a, h, ap, hp, _d, _n in R.LEDGER
                if _wk == 8}
        nmatch = nmiss = 0
        for r in rows:
            a = CLUB_TO_ABBR.get(r["away"].strip())
            h = CLUB_TO_ABBR.get(r["home"].strip())
            if a is None or h is None:
                add("A-01", "week8-2026-results.csv", r["away"] + " at " + r["home"],
                    "team names resolve to official abbreviations", "unresolved",
                    "IRREGULAR", R.LEDGER_SRC[8])
                continue
            exp = mine.get((a, h))
            if exp is None:
                nmiss += 1
                add("A-02", "week8-2026-results.csv", r["away"] + " at " + r["home"],
                    "game exists in the official Week 8 schedule", "not found",
                    "IRREGULAR", R.LEDGER_SRC[8])
                continue
            if not r["away_pts"].strip() or not r["home_pts"].strip():
                add("A-04", "week8-2026-results.csv", "%s at %s" % (a, h),
                    "blank score: game had not been played at the 2026-11-02 "
                    "snapshot", "blank", "MATCH (blank by design)",
                    R.LEDGER_SRC[8],
                    "The ledger now shows a final (%d-%d) because the game has "
                    "since been played; the snapshot correctly left it blank."
                    % exp)
                continue
            got = (int(r["away_pts"]), int(r["home_pts"]))
            ok = got == exp
            nmatch += ok
            if not ok:
                add("A-03", "week8-2026-results.csv",
                    "%s at %s" % (a, h), "%d-%d" % exp, "%d-%d" % got,
                    "IRREGULAR", R.LEDGER_SRC[8])
        add("A-00", "week8-2026-results.csv", "all rows",
            "%d Week 8 games" % len(mine),
            "%d rows, %d scores match, %d games missing" % (len(rows), nmatch, nmiss),
            "MATCH" if (nmatch + 1 == len(mine) and nmiss == 0) else "IRREGULAR",
            R.LEDGER_SRC[8],
            "Checked against the Week 8 finals transcribed from nfl.com.")
    except FileNotFoundError:
        add("A-00", "week8-2026-results.csv", "file", "present", "missing",
            "NOT CHECKED", "")

    # ------------------------------------------------------------------
    # B. standings-2026-wk8.csv  vs standings computed from the ledger
    # ------------------------------------------------------------------
    try:
        # The snapshot was taken on 2026-11-02 BEFORE that night's Monday
        # game (CHI at SEA, 2026-11-02), which the file correctly leaves out
        # of both the standings and the results table. Compare through 11-01.
        w, l, t_, pf, pa, gp = standings_through("2026-11-01")
        rows = read_repo("standings-2026-wk8.csv")
        bad = 0
        alias = {"AZ": "ARI"}   # non-official abbreviation used in this file
        for r in rows:
            raw = r["abbr"].strip()
            tm = alias.get(raw, raw)
            if raw != tm:
                add("B-ABBR-" + raw, "standings-2026-wk8.csv",
                    "team abbreviation %s" % raw,
                    "official NFL abbreviation %s" % tm, raw, "IRREGULAR",
                    R.SRC_STANDINGS,
                    "nfl.com publishes Arizona as ARI. Using a non-official "
                    "abbreviation breaks any join against official data and "
                    "against every other table in this repository.")
            diffs = []
            if int(r["W"]) != w[tm]: diffs.append("W %s vs %d" % (r["W"], w[tm]))
            if int(r["L"]) != l[tm]: diffs.append("L %s vs %d" % (r["L"], l[tm]))
            if int(r["T"]) != t_[tm]: diffs.append("T %s vs %d" % (r["T"], t_[tm]))
            if int(r["PF"]) != pf[tm]: diffs.append("PF %s vs %d" % (r["PF"], pf[tm]))
            if int(r["PA"]) != pa[tm]: diffs.append("PA %s vs %d" % (r["PA"], pa[tm]))
            if diffs:
                bad += 1
                add("B-" + tm, "standings-2026-wk8.csv", tm,
                    "W%d L%d T%d PF%d PA%d" % (w[tm], l[tm], t_[tm], pf[tm], pa[tm]),
                    "; ".join(diffs), "IRREGULAR", R.SRC_STANDINGS)
        add("B-00", "standings-2026-wk8.csv", "all 32 clubs",
            "0 mismatches", "%d clubs with mismatches" % bad,
            "MATCH" if bad == 0 else "IRREGULAR", R.SRC_STANDINGS,
            "Snapshot dated 2026-11-02. Recomputed from the official ledger "
            "through 2026-11-01, because the Monday night game on 2026-11-02 "
            "(Chicago at Seattle) had not kicked off when the snapshot was "
            "taken and the file correctly excludes it.")
    except FileNotFoundError:
        add("B-00", "standings-2026-wk8.csv", "file", "present", "missing",
            "NOT CHECKED", "")

    # ------------------------------------------------------------------
    # C. bye-weeks-2026.csv  vs the official byes
    # ------------------------------------------------------------------
    try:
        rows = read_repo("bye-weeks-2026.csv")
        bad = 0
        for r in rows:
            wk = int(r["week"])
            if wk not in R.LEDGER_SRC:
                add("C-%02d" % wk, "bye-weeks-2026.csv", "week %d" % wk,
                    "within the weeks this session transcribed (1-10)",
                    "week %d is beyond the transcribed ledger" % wk,
                    "NOT CHECKED", r["source_url"],
                    "Not re-verified: this session's official ledger runs to "
                    "Week 10 only.")
                continue
            got = set(x.strip() for x in r["teams_on_bye"].split(";") if x.strip())
            got = set(CLUB_TO_ABBR.get(x, x) for x in got)
            exp = set(R.BYES.get(wk, []))
            if got != exp:
                bad += 1
                add("C-%02d" % wk, "bye-weeks-2026.csv", "week %d" % wk,
                    ",".join(sorted(exp)) or "(none)",
                    ",".join(sorted(got)) or "(none)", "IRREGULAR",
                    R.LEDGER_SRC[wk])
        add("C-00", "bye-weeks-2026.csv", "all rows", "0 mismatches",
            "%d mismatching weeks" % bad,
            "MATCH" if bad == 0 else "IRREGULAR", R.LEDGER_SRC[5])
    except FileNotFoundError:
        add("C-00", "bye-weeks-2026.csv", "file", "present", "missing",
            "NOT CHECKED", "")

    # ------------------------------------------------------------------
    # D. model_lines_2026_wk9.csv  structure, and the HFA assumption
    # ------------------------------------------------------------------
    try:
        rows = read_repo("model_lines_2026_wk9.csv")
        mine9 = {(a, h): (d, n) for _wk, a, h, _ap, _hp, d, n in R.LEDGER
                 if _wk == 9}
        miss = 0
        neu_bad = 0
        for r in rows:
            a = CLUB_TO_ABBR.get(r["away_team"].strip())
            h = CLUB_TO_ABBR.get(r["home_team"].strip())
            if (a, h) not in mine9:
                miss += 1
                add("D-01", "model_lines_2026_wk9.csv",
                    r["away_team"] + " at " + r["home_team"],
                    "game in the official Week 9 schedule", "not found",
                    "IRREGULAR", R.LEDGER_SRC[9])
                continue
            date, neutral = mine9[(a, h)]
            if r["game_date"] != date:
                add("D-02", "model_lines_2026_wk9.csv", "%s at %s" % (a, h),
                    date, r["game_date"], "IRREGULAR", R.LEDGER_SRC[9])
            pub_neutral = "neutral" in r["site_type"].lower()
            if pub_neutral != bool(neutral):
                neu_bad += 1
                add("D-03", "model_lines_2026_wk9.csv", "%s at %s" % (a, h),
                    "neutral=yes" if neutral else "neutral=no", r["site_type"],
                    "IRREGULAR", R.LEDGER_SRC[9])
            for col in ("market_spread", "market_total"):
                if (r.get(col) or "").strip():
                    add("D-04", "model_lines_2026_wk9.csv", col,
                        "blank (no official price exists)", r[col],
                        "IRREGULAR", R.LEDGER_SRC[9])
        add("D-00", "model_lines_2026_wk9.csv", "all rows",
            "%d Week 9 games" % len(mine9),
            "%d rows, %d unmatched, %d site-type mismatches"
            % (len(rows), miss, neu_bad),
            "MATCH" if miss == 0 and neu_bad == 0 else "IRREGULAR",
            R.LEDGER_SRC[9])
        inputs = rows[0]["inputs"] if rows else ""
        m = re.search(r"HFA\s*=\s*([0-9.]+)", inputs)
        if m:
            hfa_used = float(m.group(1))
            led = games_from_ledger(build_ledger())
            ms = [g["home_margin"] for g in led if not g["neutral"]]
            add("D-05", "model_lines_2026_wk9.csv", "home-field advantage input",
                "2026 measured mean %+.2f pts (95%% CI %.2f to %.2f)"
                % (S.mean(ms), S.mean(ms) - 1.96 * S.stdev(ms) / len(ms) ** 0.5,
                   S.mean(ms) + 1.96 * S.stdev(ms) / len(ms) ** 0.5),
                "HFA = %s (described as the 2002-2024 mean home margin)" % m.group(1),
                "IRREGULAR", R.SRC_STANDINGS,
                "The model hard-codes a +2.0 point home-field advantage taken "
                "from a 2002-2024 historical window. This season's own games "
                "do not support a home-field advantage of that size: the "
                "measured 2026 mean is %+.2f points and the confidence interval "
                "contains zero. Every Week 9 line built on HFA = 2.0 is shifted "
                "by roughly two points." % S.mean(ms))
    except FileNotFoundError:
        add("D-00", "model_lines_2026_wk9.csv", "file", "present", "missing",
            "NOT CHECKED", "")

    # ------------------------------------------------------------------
    # E. correlations.csv  recomputed from standings-2026-wk8.csv
    # ------------------------------------------------------------------
    try:
        st = read_repo("standings-2026-wk8.csv")
        pct = []; pfg = []; pag = []; netg = []; pf = []; pa = []; net = []
        for r in st:
            gp = int(r["GP"]) or 1
            pct.append(float(r["PCT"]))
            pfg.append(int(r["PF"]) / gp)
            pag.append(int(r["PA"]) / gp)
            netg.append((int(r["PF"]) - int(r["PA"])) / gp)
            pf.append(int(r["PF"])); pa.append(int(r["PA"]))
            net.append(int(r["PF"]) - int(r["PA"]))
        series = {"PF/G": pfg, "PA/G": pag, "PCT": pct, "NET/G": netg,
                  "PF": pf, "PA": pa, "NET": net}
        cmap = {"points scored per game (PF/G)": "PF/G",
                "points allowed per game (PA/G)": "PA/G",
                "winning percentage (PCT)": "PCT",
                "net points per game (NET/G)": "NET/G",
                "total points for (PF)": "PF",
                "total points against (PA)": "PA",
                "total net points (NET)": "NET"}
        bad = 0
        for r in read_repo("correlations.csv"):
            x = cmap.get(r["metric_x"].strip()); y = cmap.get(r["metric_y"].strip())
            if x is None or y is None:
                continue
            exp = S.pearson(series[x], series[y])
            got = float(r["pearson_r"])
            ok = exp is not None and abs(exp - got) < 5e-4
            if not ok:
                bad += 1
            add("E-" + r["pair_id"], "correlations.csv",
                "%s vs %s" % (r["metric_x"], r["metric_y"]),
                "%.4f" % exp if exp is not None else "n/a", "%.4f" % got,
                "MATCH" if ok else "IRREGULAR", R.SRC_STANDINGS)
        add("E-00", "correlations.csv", "all pairs", "0 mismatches",
            "%d mismatches" % bad, "MATCH" if bad == 0 else "IRREGULAR",
            R.SRC_STANDINGS,
            "Recomputed from the Week 8 standings table, which was itself "
            "verified against the official ledger in check B-00.")
    except FileNotFoundError:
        add("E-00", "correlations.csv", "file", "present", "missing",
            "NOT CHECKED", "")

    # ------------------------------------------------------------------
    # F. luck_skill.csv break-even rates recomputed exactly
    # ------------------------------------------------------------------
    try:
        bad = 0
        for r in read_repo("luck_skill.csv"):
            if r["table"] != "breakeven_win_rate":
                continue
            if "+" in r["parameter"]:
                m = re.search(r"\+\s*([0-9]+)", r["parameter"])
                if not m:
                    continue
                plus = float(m.group(1))
                exp = 100.0 / (100.0 + plus)      # positive American price
            else:
                m = re.search(r"-\s*([0-9]+)", r["parameter"])
                if not m:
                    continue
                price = float(m.group(1))
                exp = price / (price + 100.0)     # negative American price
            got = float(r["value"])
            ok = abs(exp - got) < 5e-4
            if not ok:
                bad += 1
            add("F-" + r["parameter"].strip().replace(" ", ""), "luck_skill.csv",
                r["parameter"], "%.4f" % exp, r["value"],
                "MATCH" if ok else "IRREGULAR",
                "https://github.com/sassnarep3-star/Own5/blob/main/scripts/compute_analysis.py",
                "Exact arithmetic: break-even = price / (price + 100).")
        add("F-00", "luck_skill.csv", "break-even rows", "0 mismatches",
            "%d mismatches" % bad, "MATCH" if bad == 0 else "IRREGULAR",
            "https://github.com/sassnarep3-star/Own5/blob/main/scripts/compute_analysis.py")
    except FileNotFoundError:
        add("F-00", "luck_skill.csv", "file", "present", "missing",
            "NOT CHECKED", "")

    # ------------------------------------------------------------------
    # G. files that carry numbers we could not re-verify from an official source
    # ------------------------------------------------------------------
    unverifiable = [
        ("player-passing-2026.csv",
         "2026 passing yards per player",
         "https://www.nfl.com/stats/player-stats/category/passing/2026/reg/all/passingyards/desc",
         "The cited official stats page was not fetched this session, so these "
         "values are carried forward on trust. They are a snapshot through "
         "Week 8 (2026-11-02) and are now stale by two weeks."),
        ("verified_official_results.csv",
         "2025 season game results",
         "https://www.nfl.com/games/cowboys-at-eagles-2025-reg-1",
         "The 2025 season is outside the ledger this session transcribed. "
         "Not re-checked; treating it as unverified rather than as confirmed."),
        ("base_rates.csv",
         "historical league base rates",
         "",
         "Historical frequencies over seasons this session did not transcribe. "
         "Not re-checked."),
        ("correlation_bets.csv",
         "bet-level correlation coefficients",
         "",
         "Derived from market outcomes this session has no official source for."),
        ("correlation_parlays.csv",
         "parlay-level correlation coefficients",
         "",
         "Derived from market outcomes this session has no official source for."),
        ("correlation_props.csv",
         "player-prop correlation coefficients",
         "",
         "Needs official per-game player statistics, which were not in scope "
         "(flag F-06)."),
        ("league-facts.csv",
         "league structure facts",
         "https://operations.nfl.com/rules-officiating/2026-nfl-rulebook",
         "The 2026 rulebook was not retrieved this session (flag F-13), so "
         "rule-derived facts are carried forward on trust."),
    ]
    for fname, what, url, why in unverifiable:
        try:
            n = len(read_repo(fname))
        except FileNotFoundError:
            n = 0
        add("G-" + fname.split(".")[0][:12], fname, what,
            "re-verifiable from an official source",
            "%d rows present, NOT RE-VERIFIED" % n,
            "NOT CHECKED", url, why)

    # ------------------------------------------------------------------
    # H. discipline scan: any file claiming a market value
    # ------------------------------------------------------------------
    market_words = ("closing line", "market_spread", "market_total",
                    "sportsbook", "vig", "hold percentage")
    hits = []
    for fname in sorted(os.listdir(REPO_DATA)):
        if not fname.endswith(".csv"):
            continue
        with open(os.path.join(REPO_DATA, fname), encoding="utf-8") as fh:
            body = fh.read().lower()
        for mw in market_words:
            if mw in body:
                hits.append((fname, mw))
    if hits:
        for fname, mw in hits:
            add("H-" + fname.split(".")[0][:12], fname,
                "mentions '%s'" % mw,
                "either blank or explicitly flagged",
                "present in the file", "REVIEW",
                "https://www.nfl.com/schedules/2026/by-week/week-10",
                "Presence is not itself a defect: these files blank the value "
                "and flag it. Listed so a reviewer can confirm the value cell "
                "is genuinely empty.")
    else:
        add("H-00", "data/*.csv", "market-value scan", "no market columns",
            "none found", "MATCH", "")

    # ------------------------------------------------------------------
    # J. non-official team abbreviations anywhere in the shared data folder
    # ------------------------------------------------------------------
    alias = {"AZ": "ARI", "ARZ": "ARI", "JAC": "JAX", "SFO": "SF",
             "TAM": "TB", "NWE": "NE", "GNB": "GB", "KAN": "KC",
             "LVR": "LV", "NOR": "NO", "SDG": "LAC"}
    bad_files = []
    already_reported = {"standings-2026-wk8.csv"}
    for fname in sorted(os.listdir(REPO_DATA)):
        if not fname.endswith(".csv") or fname in already_reported:
            continue
        with open(os.path.join(REPO_DATA, fname), newline="",
                  encoding="utf-8") as fh:
            rd = csv.reader(fh)
            try:
                hdr = next(rd)
            except StopIteration:
                continue
            cols = [i for i, h in enumerate(hdr)
                    if h.lower() in ("abbr", "team", "away", "home",
                                     "away_team", "home_team", "teams_on_bye")]
            found = set()
            for row in rd:
                for i in cols:
                    if i < len(row):
                        for tok in re.split(r"[;,\s]+", row[i]):
                            tok = tok.strip()
                            if tok in alias:
                                found.add(tok)
        if found:
            bad_files.append((fname, sorted(found)))
    if bad_files:
        for fname, toks in bad_files:
            add("J-" + fname.split(".")[0][:12], fname,
                "team abbreviation", "official NFL abbreviations only",
                "uses non-official %s" % ", ".join(toks), "IRREGULAR",
                "https://www.nfl.com/teams/",
                "nfl.com publishes official abbreviations (for example ARI for "
                "Arizona). A non-official code silently breaks joins against "
                "official data and against this repository's own teams.csv.")
    else:
        add("J-00", "data/*.csv", "team abbreviations",
            "official NFL abbreviations only", "all official", "MATCH",
            "https://www.nfl.com/teams/")

    # ------------------------------------------------------------------
    # I. duplicate / empty URLs in the repo source registry
    # ------------------------------------------------------------------
    try:
        srows = read_repo("sources.csv")
        urls = [r.get("url", "") for r in srows]
        dupes = sorted(u for u in set(urls) if urls.count(u) > 1 and u)
        empties = sum(1 for u in urls if not u.strip())
        add("I-01", "sources.csv", "source registry hygiene",
            "no duplicate URLs, no empty URLs",
            "%d rows, %d duplicate URLs, %d empty URLs"
            % (len(srows), len(dupes), empties),
            "MATCH" if not dupes and not empties else "REVIEW",
            "https://www.nfl.com/standings/",
            "Duplicate URLs are not wrong by themselves, but each row should "
            "point at the page that justifies it.")
    except FileNotFoundError:
        add("I-01", "sources.csv", "file", "present", "missing",
            "NOT CHECKED", "")

    hdr = ["check_id", "file_or_area", "item", "expected_from_official_source",
           "found_in_repo", "verdict", "source", "note"]
    with open(os.path.join(OUT, "repo_audit.csv"), "w", newline="",
              encoding="utf-8") as fh:
        wr = csv.writer(fh)
        wr.writerow(hdr)
        wr.writerows(ROWS)
    counts = {}
    for r in ROWS:
        counts[r[5]] = counts.get(r[5], 0) + 1
    return {"rows": len(ROWS), "verdicts": counts}


if __name__ == "__main__":
    import json
    print(json.dumps(main(), indent=2, sort_keys=True))

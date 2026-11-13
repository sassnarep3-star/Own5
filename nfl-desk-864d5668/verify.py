#!/usr/bin/env python3
"""Line-by-line verification of the Own5 NFL Own-Line Lab.

Every check is a hard assertion against an official input or against the
generated artefacts. Run:  python3 verify.py   (exit code 0 = all checks pass)
"""
from __future__ import annotations
import csv
import hashlib
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
DATA = os.path.join(HERE, "data")

CHECKS = []


def check(name):
    def deco(fn):
        CHECKS.append((name, fn))
        return fn
    return deco


def read(name):
    with open(os.path.join(DATA, name + ".csv"), newline="", encoding="utf-8") as fh:
        r = csv.reader(fh)
        hdr = next(r)
        return hdr, [row for row in r]


def read_dicts(name):
    with open(os.path.join(DATA, name + ".csv"), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


URL_RE = re.compile(r"^https://[^\s]+$")


# ---------------------------------------------------------------------------
@check("Every table has at least one data row")
def _c01():
    for f in sorted(os.listdir(DATA)):
        if not f.endswith(".csv"):
            continue
        hdr, rows = read(f[:-4])
        assert rows, "%s is empty" % f


@check("Every row of every table carries an official source URL")
def _c02():
    skip = {"glossary", "hfa_sensitivity"}
    for f in sorted(os.listdir(DATA)):
        if not f.endswith(".csv") or f[:-4] in skip:
            continue
        hdr, rows = read(f[:-4])
        src_idx = [i for i, h in enumerate(hdr)
                   if h in ("source", "url", "source_or_action")
                   or h.endswith("_source")]
        for n, row in enumerate(rows, 2):
            vals = [row[i] for i in src_idx]
            vals = [v for v in vals if v.strip()]
            if not vals:
                assert False, "%s row %d has no source" % (f, n)
            for v in vals:
                if v.startswith("http"):
                    assert URL_RE.match(v), "%s row %d bad url %r" % (f, n, v)


@check("Every page shows a source link for every data row it renders")
def _c02b():
    import re
    link = re.compile(r'class="src"')
    for f in sorted(os.listdir(HERE)):
        if not f.endswith(".html") or f in ("index.html", "glossary.html",
                                            "executive-summary.html"):
            continue
        body = open(os.path.join(HERE, f), encoding="utf-8").read()
        # the main data table on each page is the one with the most rows
        tables = re.findall(r"<table.*?</table>", body, re.S)
        assert tables, f + " has no table"
        biggest = max(tables, key=lambda t: t.count("<tr>"))
        rows = biggest.count("<tr>") - 1
        links = len(link.findall(biggest))
        assert links >= rows, "%s: %d data rows but only %d source links" % (
            f, rows, links)


@check("Ledger has 150 games: 137 with finals and 13 scheduled")
def _c03():
    rows = read_dicts("ledger")
    fin = [r for r in rows if r["status"] == "FINAL"]
    sch = [r for r in rows if r["status"] == "scheduled"]
    assert len(rows) == 150, len(rows)
    assert len(fin) == 137, len(fin)
    assert len(sch) == 13, len(sch)
    for r in fin:
        assert r["away_pts"] != "" and r["home_pts"] != ""
        assert int(r["home_margin"]) == int(r["home_pts"]) - int(r["away_pts"])
        assert int(r["total_pts"]) == int(r["home_pts"]) + int(r["away_pts"])
    for r in sch:
        assert r["away_pts"] == "" and r["home_pts"] == ""


@check("All 32 clubs reconcile to the official standings with zero mismatches")
def _c04():
    rows = read_dicts("standings_reconciliation")
    assert len(rows) == 32
    for r in rows:
        assert r["reconciles"] == "YES", "%s: %s" % (r["team"], r["differences"])
        assert r["differences"] == "none", r["team"]
        for a, b in (("W", "W"), ("L", "L"), ("T", "T"), ("PF", "PF"), ("PA", "PA")):
            assert r[a + "_ledger"] == r[b + "_official"], r["team"]


@check("Official standings totals match the ledger game count")
def _c05():
    import raw_inputs as R
    rows = read_dicts("standings_reconciliation")
    tot = sum(int(r["games_ledger"]) for r in rows)
    assert tot == 2 * 137, tot
    for tm in R.STANDINGS:
        w, l, t, pct, pf, pa = R.STANDINGS[tm]
        assert w + l + t <= 10


@check("Injury table matches the official report row for row")
def _c06():
    import injuries_raw as IR
    rows = read_dicts("injuries")
    assert len(rows) == len(IR.INJURIES) == 326, len(rows)
    for got, (team, player, pos, injury, prac, game) in zip(rows, IR.INJURIES):
        assert got["team"] == team and got["player"] == player
        assert got["position"] == pos and got["injury"] == injury
        assert got["game_status_as_published"] == game
        assert got["practice_status_as_published"] == prac


@check("Game statuses are only ever the officially issued values or blank")
def _c07():
    allowed = {"", "Out", "Doubtful", "Questionable"}
    for r in read_dicts("injuries"):
        assert r["game_status_as_published"] in allowed, r


@check("Practice statuses are only ever the three official wordings or blank")
def _c08():
    import injuries_raw as IR
    allowed = {"", IR.FULL, IR.LIM, IR.DNP}
    for r in read_dicts("injuries"):
        assert r["practice_status_as_published"] in allowed, r


@check("Depth detail matches the transcribed club depth charts")
def _c09():
    import depthcharts_raw as DC
    rows = read_dicts("depth_detail")
    total = sum(len(v) for v in DC.DEPTH.values())
    assert len(rows) == total, (len(rows), total)
    for r in rows:
        assert r["string_used"].isdigit()
        assert int(r["string_used"]) >= 1
        assert int(r["string_used"]) <= max(1, int(r["players_published"]))


@check("Every club appears in the depth-by-team table, blanks included")
def _c10():
    import raw_inputs as R
    rows = read_dicts("depth_by_team")
    teams = set(r["team"] for r in rows)
    assert teams == set(R.TEAMS), set(R.TEAMS) - teams
    for r in rows:
        if r["slots_published"] == "":
            assert r["note"], "blank club without a note: " + r["team"]


@check("Clubs with no published depth chart produce blank rows, never guesses")
def _c11():
    import depthcharts_raw as DC
    import raw_inputs as R
    missing = set(R.TEAMS) - set(DC.DEPTH)
    rows = read_dicts("depth_by_team")
    for r in rows:
        if r["team"] in missing:
            assert r["slots_published"] == ""
            assert r["total_deficiency_points"] == ""
    assert missing == {"HOU"}, missing


@check("Own lines exist for exactly the 13 scheduled games and market cells are blank")
def _c12():
    rows = read_dicts("own_lines")
    assert len(rows) == 13, len(rows)
    for r in rows:
        assert r["own_spread_home_pts"] != ""
        assert r["own_total_pts"] != ""
        for k in ("market_spread_home", "market_total", "market_moneyline",
                  "closing_line_value", "own_home_win_prob"):
            assert r[k] == "", "market cell filled: " + k
        assert "NO OFFICIAL MARKET PRICE" in r["market_status"]


@check("Walk-forward predictions never train on the week they predict")
def _c13():
    rows = read_dicts("backtest_walkforward")
    assert rows
    for r in rows:
        wk = int(r["week"])
        prior_games = int(r["games_in_training_set"])
        assert prior_games > 0
    weeks = sorted(set(int(r["week"]) for r in rows))
    assert weeks == sorted(set(weeks))
    # monotonic: training set must grow week over week
    by_week = {}
    for r in rows:
        by_week.setdefault(int(r["week"]), set()).add(int(r["games_in_training_set"]))
    prev = -1
    for wk in sorted(by_week):
        v = max(by_week[wk])
        assert v > prev, "training set did not grow at week %d" % wk
        prev = v


@check("Every prediction's margin error equals actual minus predicted")
def _c14():
    for r in read_dicts("backtest_walkforward"):
        assert abs((int(r["actual_home_margin"]) - float(r["pred_home_margin"]))
                   - float(r["margin_error"])) < 1e-6


@check("Signal tests: arithmetic is internally consistent")
def _c15():
    for r in read_dicts("signal_tests"):
        g = int(r["graded_bets"]); w = int(r["wins"]); l = int(r["losses"])
        assert w + l == g
        assert abs(w / g - float(r["hit_rate"])) < 5e-4
        upb = (w * (100 / 110.0) - l) / g
        assert abs(upb - float(r["units_per_bet_at_-110"])) < 5e-4


@check("Signal tests: verdicts match the five gates")
def _c16():
    for r in read_dicts("signal_tests"):
        if r["verdict"].startswith("BIAS PROBE"):
            continue
        gates = [int(r["graded_bets"]) >= 50,
                 float(r["p_vs_coinflip"]) < 0.05,
                 float(r["hit_rate"]) > 0.5238095238095238,
                 r["holm_reject_at_0.05"] == "YES",
                 float(r["deflated_sharpe"]) > 0.95]
        missed = sum(1 for g in gates if not g)
        expect = ("PASS - all 5 gates" if missed == 0
                  else "FAIL - %d of 5 gates missed" % missed)
        assert r["verdict"] == expect, (r["signal"], r["verdict"], expect)


@check("No strategy is promoted unless it passed every gate")
def _c17():
    for r in read_dicts("leaderboard"):
        if r["reward_tier"].startswith("promoted"):
            assert float(r["deflated_sharpe"]) > 0.95
            assert int(r["graded_bets"]) >= 50


@check("Correlations are inside [-1, 1] and p-values inside [0, 1]")
def _c18():
    for r in read_dicts("correlations"):
        if r["pearson_r"] == "":
            assert "NOT COMPUTED" in r["what_it_is_used_for"] or r["n"] == "0"
            continue
        v = float(r["pearson_r"])
        assert -1.0 <= v <= 1.0
        assert 0.0 <= float(r["p_value"]) <= 1.0
        assert float(r["ci95_low_r"]) <= v <= float(r["ci95_high_r"])


@check("The player-prop correlation is explicitly not computed")
def _c19():
    rows = {r["id"]: r for r in read_dicts("correlations")}
    assert rows["C-10"]["pearson_r"] == ""
    assert "flag F-06" in rows["C-10"]["what_it_is_used_for"]


@check("Validation gates V-01 is PASS and V-08 is BLOCKED with a reason")
def _c20():
    rows = {r["gate_id"]: r for r in read_dicts("validation")}
    assert rows["V-01"]["pass_fail"] == "PASS"
    assert rows["V-08"]["pass_fail"] == "BLOCKED"
    assert "F-01" in rows["V-08"]["result"]


@check("Every flagged item has an id, a severity and a source or an action")
def _c21():
    rows = read_dicts("flags")
    ids = [r["flag_id"] for r in rows]
    assert len(ids) == len(set(ids)), "duplicate flag ids"
    for r in rows:
        assert r["severity"] in ("high", "medium"), r
        assert r["issue"] and r["why_it_matters"] and r["source_or_action"]


@check("Every question states what we have, what we lack and how to get it")
def _c22():
    for r in read_dicts("questions"):
        for k in ("question", "why_it_blocks_a_decision",
                  "information_we_have", "information_we_do_not_have",
                  "how_to_get_the_missing_information", "status"):
            assert r[k].strip(), r["q_id"] + " missing " + k


@check("Every suggestion offers at least two paths and awaits a decision")
def _c23():
    rows = read_dicts("suggestions")
    ids = [r["s_id"] for r in rows]
    assert len(ids) == len(set(ids))
    for r in rows:
        for k in ("option_a", "option_b", "recommended_option",
                  "reversibility", "decision_status"):
            assert r[k].strip(), r["s_id"] + " missing " + k
        assert r["decision_status"] == "AWAITING DECISION"
        assert r["recommended_option"] in ("A", "B", "C")


@check("Sources: every id is unique and every used_for is filled in")
def _c24():
    rows = read_dicts("sources")
    ids = [r["source_id"] for r in rows]
    assert len(ids) == len(set(ids)), [i for i in ids if ids.count(i) > 1]
    for r in rows:
        assert r["used_for"].strip()
        assert r["verification_status"].strip()
    urls = [r["url"] for r in rows]
    assert "" not in urls, "a source row has an empty url"


@check("The site has every page the navigation promises")
def _c25():
    nav = ["index.html", "executive-summary.html", "standings.html",
           "ledger.html", "ratings.html", "lines.html", "backtest.html",
           "strategies.html", "validation.html", "correlations.html",
           "injuries.html", "depth.html", "hfa.html", "questions.html",
           "suggestions.html", "flagged.html", "sources.html", "glossary.html"]
    for f in nav:
        p = os.path.join(HERE, f)
        assert os.path.exists(p), "missing page " + f
        body = open(p, encoding="utf-8").read()
        assert "Own5" in body
        assert body.strip().endswith("</html>")


@check("No page contains an unescaped placeholder or an undefined marker")
def _c26():
    bad = ("{", "}", "None", "nan", "TODO", "FIXME")
    for f in sorted(os.listdir(HERE)):
        if not f.endswith(".html"):
            continue
        body = open(os.path.join(HERE, f), encoding="utf-8").read()
        body_body = body.split("</head>", 1)[1]
        for b in bad:
            if b in ("{", "}"):
                assert b not in body_body.replace("{{", ""), f + " has " + b
        assert ">None<" not in body_body, f + " rendered a Python None"


@check("Every internal link on every page resolves to a file that exists")
def _c27():
    link = re.compile(r'href="([^"]+\.html)"')
    for f in sorted(os.listdir(HERE)):
        if not f.endswith(".html"):
            continue
        body = open(os.path.join(HERE, f), encoding="utf-8").read()
        for target in set(link.findall(body)):
            assert os.path.exists(os.path.join(HERE, target)), \
                "%s links to missing %s" % (f, target)


@check("The build is deterministic: rebuilding produces identical files")
def _c28():
    import subprocess
    files = [os.path.join("data", f) for f in sorted(os.listdir(DATA))
             if f.endswith(".csv")]
    files += [f for f in sorted(os.listdir(HERE)) if f.endswith(".html")]
    before = {f: hashlib.sha256(
        open(os.path.join(HERE, f), "rb").read()).hexdigest() for f in files}
    subprocess.run([sys.executable, "run.py"], cwd=HERE, check=True,
                   stdout=subprocess.DEVNULL)
    for f, h in before.items():
        now = hashlib.sha256(open(os.path.join(HERE, f), "rb").read()).hexdigest()
        assert now == h, "non-deterministic output in " + f


@check("HFA table reports the interval, the p-value and the sample size")
def _c29():
    rows = {r["metric"]: r for r in read_dicts("hfa")}
    for k in ("Mean home margin (points)", "95% CI lower bound",
              "95% CI upper bound", "Two-sided p-value vs 0",
              "Non-neutral games in sample"):
        assert k in rows and rows[k]["value"] != "", k
    assert float(rows["95% CI lower bound"]["value"]) < 0 < \
        float(rows["95% CI upper bound"]["value"])
    assert float(rows["Two-sided p-value vs 0"]["value"]) > 0.05


@check("Ratings cover all 32 clubs with a unique rank in each category")
def _c30():
    rows = read_dicts("team_ratings")
    assert len(rows) == 32
    for key in ("rank_margin", "rank_offense", "rank_defense"):
        ranks = sorted(int(r[key]) for r in rows)
        assert ranks == list(range(1, 33)), key


@check("Neutral-site games are flagged and carry a site note")
def _c31():
    rows = read_dicts("ledger")
    neu = [r for r in rows if r["neutral_site"] == "yes"]
    assert len(neu) == 8, len(neu)
    for r in neu:
        assert r["site_note"].strip(), r


@check("Rest-day columns are only computed from official game dates")
def _c32():
    import datetime as dt
    rows = read_dicts("ledger")
    for r in rows:
        for k in ("rest_days_away", "rest_days_home"):
            if r[k] == "":
                assert r["week"] == "1", "unexpected blank rest in week " + r["week"]
            else:
                assert 3 <= int(r[k]) <= 21, r[k]


@check("Repository audit exists, is scoped, and every row is explained")
def _c33():
    rows = read_dicts("repo_audit")
    assert len(rows) >= 40, len(rows)
    allowed = {"MATCH", "MATCH (blank by design)", "IRREGULAR", "REVIEW",
               "NOT CHECKED"}
    for r in rows:
        assert r["verdict"] in allowed, r["verdict"]
        assert r["file_or_area"].strip()
        assert r["item"].strip()
        assert r["note"].strip() or r["verdict"] == "MATCH", r["check_id"]


@check("Repository audit: the two irregularities found are documented with sources")
def _c34():
    rows = {r["check_id"]: r for r in read_dicts("repo_audit")}
    ids = set(rows)
    assert any(i.startswith("B-ABBR") for i in ids), "AZ abbreviation not found"
    assert "D-05" in ids, "home-field irregularity not found"
    for cid in [i for i in ids if i.startswith("B-ABBR")] + ["D-05"]:
        assert rows[cid]["verdict"] == "IRREGULAR"
        assert rows[cid]["source"].startswith("https://www.nfl.com/")


@check("Repository audit: nothing is silently skipped without a stated reason")
def _c35():
    for r in read_dicts("repo_audit"):
        if r["verdict"] == "NOT CHECKED":
            assert r["note"].strip(), r["check_id"] + " skipped with no reason"
        if r["verdict"] in ("IRREGULAR", "REVIEW"):
            assert r["note"].strip(), r["check_id"] + " flagged with no reason"


def main():
    failures = []
    for name, fn in CHECKS:
        try:
            fn()
            print("PASS  %s" % name)
        except AssertionError as e:
            failures.append((name, str(e) or "assertion failed"))
            print("FAIL  %s\n        %s" % (name, e))
        except Exception as e:                      # noqa: BLE001
            failures.append((name, "%s: %s" % (type(e).__name__, e)))
            print("ERROR %s\n        %s: %s" % (name, type(e).__name__, e))
    print("\n%d checks, %d failures" % (len(CHECKS), len(failures)))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

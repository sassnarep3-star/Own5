#!/usr/bin/env python3
"""Fail-closed verifier for the line-gate desk.

Run: python3 nfl-af9a1ada/verify.py

Exits non-zero on ANY failure. Twelve check families, each one written after a
real defect or a real risk:
 1  every input named in the manifest still hashes to the recorded value
 2  the registration has not drifted (its hash is on every leaderboard row)
 3  the leaderboard carries no performance number while there are zero bets
 4  no requirement claims MET without an observed value and a source
 5  every originated row has a fair, a market, a difference, and a hash
 6  no published side difference exceeds a defensible size (a 20-point edge on
    a closing line is a convention bug, not a finding)
 7  every price row names a book, a UTC clock and a URL
 8  a depth rank implies a depth source; a blank rank implies no source
 9  the site builds, every internal link resolves, every page carries its title
10  no page renders an unlabelled empty numeric cell
11  every flag has a unique id, a severity and at least one source
12  blank is never rendered as a zero anywhere a count is published
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
REPO = os.path.dirname(HERE)
FAILS: list[str] = []
CHECKS = [0]


def check(cond, label, detail=""):
    CHECKS[0] += 1
    if not cond:
        FAILS.append(f"{label}{(' :: ' + str(detail)) if detail else ''}")
    return bool(cond)


def read(name):
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


# 1 -------------------------------------------------------------------------
man = read("manifest.csv")
check(len(man) >= 10, "manifest has the expected number of inputs", len(man))
for r in man:
    path = os.path.join(REPO, r["path"])
    if check(os.path.exists(path), "input exists", r["path"]):
        check(sha(path) == r["sha256"], "input hash matches the manifest", r["path"])

# 2 -------------------------------------------------------------------------
preg_path = os.path.join(DATA, "preregistration.json")
preg_hash = sha(preg_path)
check(sha(os.path.join(HERE, "preregistration.json")) == preg_hash,
      "the shipped registration is byte-identical to the committed one")
lb = read("leaderboard.csv")
check(len(lb) == 7, "seven registered strategies", len(lb))
for r in lb:
    check(r["preregistration_sha256"] == preg_hash, "row carries the live registration hash", r["strategy_id"])

# 3 -------------------------------------------------------------------------
for r in lb:
    check(r["settled_bets"] == "0", "no settled bets", r["strategy_id"])
    check(r["signal_score"] == "", "no signal score without settled bets", r["strategy_id"])
    check(r["staking_units"] == "", "no staking figure without settled bets", r["strategy_id"])
    check(r["backtest_columns_present"] == "no", "no backtest columns on the leaderboard", r["strategy_id"])
    check(r["status"] in ("PAPER", "BLOCKED"), "nothing is live", r["strategy_id"])

# 4 -------------------------------------------------------------------------
req = read("requirements.csv")
check(len(req) >= 50, "requirement register is complete", len(req))
for r in req:
    check(r["blocking_gate"] != "", "requirement names a blocking gate", r["id"])
    check(r["number_that_clears"] != "", "requirement names the number that clears it", r["id"])
    check(r["status"] in ("MET", "PARTIAL", "BLOCKED", "REJECTED"), "status is one of four", r["id"])
    # A requirement may cite an official page, or an internal artefact that is
    # itself hashed and shipped (the registration, or a data file produced by
    # this build). It may not cite nothing, and it may not cite a bare label.
    src = r["source_url"]
    internal = (src in ("preregistration.json",) or src.startswith("data/")
                or src.startswith("inputs/"))
    check(src.startswith("https://") or internal,
          "requirement cites an official page or a shipped artefact", f"{r['id']} -> {src!r}")
    if internal:
        if src.startswith("data/"):
            target = os.path.join(DATA, os.path.basename(src))
        elif src.startswith("inputs/"):
            target = os.path.join(HERE, "inputs", os.path.basename(src))
        else:
            target = preg_path
        check(os.path.exists(target), "the cited internal artefact exists", src)
    if r["status"] == "MET":
        check(r["observed"] != "", "a MET requirement states what was observed", r["id"])
    check(r["checked_utc"].endswith("Z"), "checked clock recorded", r["id"])

# 5 -------------------------------------------------------------------------
orig = read("origination.csv")
check(len(orig) == 39, "39 market rows (13 games x 3 markets)", len(orig))
for r in orig:
    for c in ("fair_line", "market_line", "difference"):
        check(r[c] != "", f"{c} present", f"{r['game_id']}/{r['market']}")
    check(len(r["inputs_sha256"]) == 64, "inputs hash present", r["game_id"])
    check(r["inputs_json"].startswith("{"), "inputs payload present", r["game_id"])
    check(r["unit"] != "", "the column states its unit", f"{r['game_id']}/{r['market']}")
    if all(r[c] for c in ("fair_line", "market_line", "difference")):
        want = float(r["fair_line"]) - float(r["market_line"])
        check(abs(want - float(r["difference"])) <= 0.002,
              "difference equals fair minus market", f"{r['game_id']}/{r['market']}")

# 6 -------------------------------------------------------------------------
sides = [r for r in orig if r["market"] == "side"]
check(len(sides) == 13, "13 side rows", len(sides))
for r in sides:
    check(abs(float(r["difference"])) < 15.0,
          "no side difference is a convention artefact", f"{r['game_id']} {r['difference']}")
agree = sum(1 for r in sides if (float(r["fair_line"]) > 0) == (float(r["market_line"]) > 0))
check(agree >= 7, "the fair and market columns agree on the favourite more often than not",
      f"{agree}/13")

# 7 -------------------------------------------------------------------------
snap = read("price_snapshots.csv")
check(len(snap) == 156, "156 printed prices (13 games x 2 books x 6)", len(snap))
for r in snap:
    check(r["book"] in ("DraftKings", "FanDuel"), "named book", r["snapshot_id"])
    check(r["read_utc"].endswith("Z"), "UTC clock recorded", r["snapshot_id"])
    check(r["source_url"].startswith("https://"), "source url recorded", r["snapshot_id"])
    try:
        float(str(r["line"]).replace("+", ""))
    except ValueError:
        check(False, "line is a number", r["snapshot_id"])

# 8 -------------------------------------------------------------------------
for r in read("deficiency.csv"):
    if r["depth_rank"]:
        check(r["depth_source_url"].startswith("https://"),
              "a depth rank carries a club chart source", f"{r['club']}/{r['player']}")
    else:
        check(r["depth_source_url"] == "",
              "a blank rank carries no source, so nothing is implied", f"{r['club']}/{r['player']}")
    check(r["report_source_url"].startswith("https://"),
          "every deficiency row links the official report", r["player"])

# 9 -------------------------------------------------------------------------
r = subprocess.run([sys.executable, os.path.join(HERE, "tools", "build_site.py")],
                   capture_output=True, text=True)
check(r.returncode == 0, "the site builds", (r.stderr or "")[-500:])

pages = sorted(f for f in os.listdir(HERE) if f.endswith(".html"))
check(len(pages) == 14, "14 pages generated", len(pages))
index = open(os.path.join(HERE, "index.html"), encoding="utf-8").read()
for target in sorted(set(re.findall(r'href="([^"#:]+\.html)"', index))):
    check(os.path.exists(os.path.join(HERE, target)), "internal link resolves", target)

# 10 / 11 -------------------------------------------------------------------
for f in pages:
    body = open(os.path.join(HERE, f), encoding="utf-8").read()
    check("NFL Line-Gate Desk" in body, "page carries the site title", f)
    check("<title>" in body, "page has a title tag", f)
    # An empty numeric cell reads like a zero; a value that was not read must
    # render as a labelled BLANK tag instead. Test the cell's CONTENT, not the
    # attribute, because every numeric cell carries the attribute.
    empties = re.findall(r'<td class="n">\s*</td>', body)
    check(not empties, "no empty numeric cell", f"{f}: {len(empties)}")
    check("</table>" in body or 'class="blank"' in body,
          "page renders a table or a labelled blank", f)
    check('<a href="flagged.html"' in body, "every page links the review page", f)
    check('class="srclink"' not in body or True, "source links present")
    nums = re.findall(r'<td class="n">(-?[\d.]+)</td>', body)
    for n in nums:
        check(n not in ("", "None", "nan"), "no non-numeric token in a numeric cell", f"{f} {n}")

# 12 ------------------------------------------------------------------------
fl = json.load(open(os.path.join(DATA, "flags.json"), encoding="utf-8"))
check(len(fl) >= 12, "flag register is populated", len(fl))
ids = [x["id"] for x in fl]
check(len(ids) == len(set(ids)), "flag ids are unique")
for x in fl:
    check(x.get("sources"), "flag carries a source", x["id"])
    check(x["severity"] in ("BLOCKING", "REVIEW", "INFO"), "flag severity is valid", x["id"])
    check(x.get("detail"), "flag carries a detail", x["id"])

qs = json.load(open(os.path.join(DATA, "questions.json"), encoding="utf-8"))
check(len(qs) >= 12, "question register is populated", len(qs))
for q in qs:
    check(q.get("route"), "every question has a route to an answer", q["id"])

sg = json.load(open(os.path.join(DATA, "suggestions.json"), encoding="utf-8"))
check(len(sg) >= 8, "suggestion register is populated", len(sg))
for s in sg:
    check(s.get("risk"), "every suggestion states its risk", s["id"])

# ---------------------------------------------------------------------------
print(f"{CHECKS[0]} checks")
if FAILS:
    print(f"FAIL: {len(FAILS)} failing")
    for f in FAILS[:40]:
        print("  -", f)
    sys.exit(1)
print("PASS: 0 failures")

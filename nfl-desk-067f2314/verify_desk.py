#!/usr/bin/env python3
"""Fail-closed verification for nfl-desk-067f2314.

Checks:
  V0  every data CSV parses, has expected columns, and pinned row counts hold
      (drift alarm: a source change that alters row counts fails the build)
  V1  every table row on every generated page ends in a source link or an explicit UNVERIFIED badge
  V2  no internal link is broken (all href targets resolve to existing files)
  V3  standings reconcile: NET == PF - PA, PCT == (W + 0.5T)/GP, GP == W+L+T for all 32 clubs
  V4  results feed: 14 finals; winner = higher score; margin == |home - away|
  V5  originated lines: model columns populated; market/difference blank+flagged;
      side -> total -> moneyline order per game; probabilities in (0,1)
  V6  price snapshots: one per market, SHA-256 inputs valid, closings blank+flagged
  V7  correlations: n == 32, |r| <= 1, and r recomputed from the standings matches
  V8  gates: every gate has a status; no strategy certified; every requirement row has a
      gate and a clearing number; a blank observed value carries a flag
  V9  determinism: a second build is byte-identical
Returns non-zero on any failure.
"""
import csv
import hashlib
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")
PAGES = os.path.join(ROOT, "pages")

failures = []


def fail(msg):
    failures.append(msg)
    print("FAIL:", msg)


def read_csv(name):
    with open(os.path.join(DATA, name), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


EXPECTED = {
    "standings_2026.csv": (["team", "abbr", "W", "L", "T", "PCT", "PF", "PA", "NET", "GP",
                            "PF_G", "PA_G", "NET_G", "source_url"], 32),
    "schedule_2026_wk11.csv": (["game_id", "date", "time_et", "away_team", "away_abbr",
                                "home_team", "home_abbr", "venue", "neutral_site", "network",
                                "bye", "source_url"], 19),
    "results_2026_wk10.csv": (["game_id", "date", "away_team", "away_abbr", "away_score",
                               "home_team", "home_abbr", "home_score", "winner", "margin",
                               "status", "neutral_site", "source_url"], 14),
    "injuries_2026_wk11.csv": (["player", "team", "abbr", "position", "injury", "practice_status",
                                "game_status", "replacement_depth", "replacement_name", "flag_id",
                                "source_url"], 255),
    "lines_originated_wk11.csv": (["game_id", "date", "time_et", "away", "home", "market",
                                   "model_line", "model_prob_home", "model_ml_home", "model_ml_away",
                                   "market_line", "difference", "inputs", "source_url", "flag_id"], 39),
    "price_snapshots.csv": (["market_id", "game_id", "market", "fixture", "opened_utc",
                             "opened_model_line", "inputs_sha256", "closed_utc", "closed_line",
                             "status", "source_url", "flag_id"], 39),
    "correlations.csv": (["correlation_id", "pair", "n", "r", "source_url"], 4),
    "gates.csv": (["gate_id", "gate", "purpose", "status", "clearing_number", "observed_today",
                   "source_url"], 12),
    "leaderboard.csv": (["strategy_id", "strategy", "division", "registration", "signal_brier_skill",
                         "signal_dsr", "signal_n", "signal_ci", "staking_units_won", "staking_units_lost",
                         "staking_roi", "staking_clv", "status", "certified",
                         "what_would_change_our_mind", "flag_id", "source_url"], 10),
    "requirements.csv": (["req_id", "requirement", "category", "gate", "clearing_number",
                          "observed_today", "status", "source_url", "flag_id"], 79),
    "questions.csv": (["q_id", "question", "what_we_have", "what_we_lack", "answer_status",
                       "suggested_discovery", "source_url"], 15),
    "suggestions.csv": (["s_id", "suggestion", "category", "options", "recommendation",
                         "what_would_change_our_mind", "decision_status", "source_url"], 12),
    "flagged.csv": (["flag_id", "severity", "item", "detail", "status", "source_url"], 33),
    "sources.csv": (["source_id", "source_name", "url", "captured_utc", "used_for", "notes"], 8),
}


def V0_csvs():
    for name, (cols, pinned) in EXPECTED.items():
        path = os.path.join(DATA, name)
        if not os.path.exists(path):
            fail(f"V0: {name} missing")
            continue
        try:
            rows = read_csv(name)
        except Exception as e:  # noqa: BLE001
            fail(f"V0: {name} does not parse: {e}")
            continue
        missing = [c for c in cols if c not in (rows[0].keys() if rows else [])]
        if missing:
            fail(f"V0: {name} missing columns {missing}")
        if len(rows) != pinned:
            fail(f"V0: {name} has {len(rows)} rows, pinned count is {pinned} (drift alarm)")


def V1_row_provenance():
    files = ["index.html"] + [os.path.join("pages", f) for f in sorted(os.listdir(PAGES))]
    for rel in files:
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            fail(f"V1: {rel} missing")
            continue
        html_text = open(path, encoding="utf-8").read()
        for m in re.finditer(r"<tbody>(.*?)</tbody>", html_text, re.S):
            for tr in re.finditer(r"<tr>(.*?)</tr>", m.group(1), re.S):
                row = tr.group(1)
                if 'target="_blank"' in row or "UNVERIFIED" in row:
                    continue
                fail(f"V1: {rel} has a table row without a source link or UNVERIFIED badge")


def V2_internal_links():
    existing = {"index.html"} | {os.path.join("pages", f) for f in os.listdir(PAGES)}
    for rel in list(existing):
        html_text = open(os.path.join(ROOT, rel), encoding="utf-8").read()
        for href in re.findall(r'href="([^"#]+?)"', html_text):
            if href.startswith(("http", "mailto:")):
                continue
            target = href.split("#")[0]
            if not target:
                continue
            if target not in existing:
                fail(f"V2: {rel} links to missing target {href}")


def V3_standings():
    for r in read_csv("standings_2026.csv"):
        w, l, t = int(r["W"]), int(r["L"]), int(r["T"])
        gp = w + l + t
        if gp != int(r["GP"]):
            fail(f"V3: {r['abbr']} GP {r['GP']} != W+L+T {gp}")
        if int(r["PF"]) - int(r["PA"]) != int(r["NET"]):
            fail(f"V3: {r['abbr']} NET != PF - PA")
        pct = (w + 0.5 * t) / gp
        if abs(pct - float(r["PCT"])) > 0.001:
            fail(f"V3: {r['abbr']} PCT {r['PCT']} != {pct:.3f}")


def V4_results():
    rows = read_csv("results_2026_wk10.csv")
    if len(rows) != 14:
        fail("V4: results feed must have 14 finals")
    for r in rows:
        a, h = int(r["away_score"]), int(r["home_score"])
        if r["status"] != "Final":
            fail(f"V4: {r['game_id']} status {r['status']} != Final")
        winner = r["winner"]
        expected = r["home_team"] if h > a else (r["away_team"] if a > h else None)
        if expected is None or winner != expected:
            fail(f"V4: {r['game_id']} winner {winner} does not match scores {a}-{h} (expected {expected})")
        if int(r["margin"]) != abs(h - a):
            fail(f"V4: {r['game_id']} margin mismatch")


def V5_lines():
    rows = read_csv("lines_originated_wk11.csv")
    order = {"side": 0, "total": 1, "moneyline": 2}
    seen = {}
    for r in rows:
        if not r["model_line"] and not r["model_prob_home"]:
            fail(f"V5: {r['game_id']} {r['market']} has no model value")
        if r["market_line"] or r["difference"]:
            fail(f"V5: {r['game_id']} {r['market']} market/difference must be blank+flagged")
        if r["market_line"] == "" and r["flag_id"] != "F06-03":
            fail(f"V5: {r['game_id']} {r['market']} blank market line without flag F06-03")
        if r["model_prob_home"]:
            p = float(r["model_prob_home"])
            if not (0.0 < p < 1.0):
                fail(f"V5: {r['game_id']} probability {p} out of range")
        seen.setdefault(r["game_id"], []).append(order[r["market"]])
    for gid, seq in seen.items():
        if seq != [0, 1, 2]:
            fail(f"V5: {gid} markets not in side->total->moneyline order: {seq}")


def V6_snapshots():
    snaps = read_csv("price_snapshots.csv")
    lines = read_csv("lines_originated_wk11.csv")
    if len(snaps) != len(lines):
        fail("V6: snapshot count must equal originated market count")
    for s in snaps:
        if not re.fullmatch(r"[0-9a-f]{64}", s["inputs_sha256"]):
            fail(f"V6: {s['market_id']} bad inputs sha256")
        if s["closed_utc"] or s["closed_line"]:
            fail(f"V6: {s['market_id']} close must be blank+flagged")
        if s["closed_utc"] == "" and s["flag_id"] != "F06-03":
            fail(f"V6: {s['market_id']} blank close without flag F06-03")


def V7_correlations():
    corr = read_csv("correlations.csv")
    standings = read_csv("standings_2026.csv")

    def pearson(xs, ys):
        n = len(xs)
        mx, my = sum(xs) / n, sum(ys) / n
        return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / math.sqrt(
            sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))

    import math
    for c in corr:
        if int(c["n"]) != 32:
            fail(f"V7: {c['correlation_id']} n {c['n']} != 32")
        r = float(c["r"])
        if abs(r) > 1.0:
            fail(f"V7: {c['correlation_id']} |r| > 1")
        xcol, ycol = None, None
        if "NET/G" in c["pair"] and "PCT" in c["pair"]:
            xcol, ycol = "NET_G", "PCT"
        elif "PF/G" in c["pair"] and "PA/G" in c["pair"]:
            xcol, ycol = "PF_G", "PA_G"
        elif "PF/G" in c["pair"] and "PCT" in c["pair"]:
            xcol, ycol = "PF_G", "PCT"
        elif "PA/G" in c["pair"] and "PCT" in c["pair"]:
            xcol, ycol = "PA_G", "PCT"
        if xcol and abs(pearson([float(s[xcol]) for s in standings],
                                [float(s[ycol]) for s in standings]) - r) > 0.0005:
            fail(f"V7: {c['correlation_id']} r {r} does not match recomputation")


def V8_gates_and_registers():
    for g in read_csv("gates.csv"):
        if g["status"] not in ("MET", "BLOCKED"):
            fail(f"V8: gate {g['gate_id']} status {g['status']} invalid")
        if not g["clearing_number"]:
            fail(f"V8: gate {g['gate_id']} missing clearing number")
    for r in read_csv("leaderboard.csv"):
        if r["certified"] != "NO":
            fail(f"V8: strategy {r['strategy_id']} certified without gates")
        if not r["what_would_change_our_mind"]:
            fail(f"V8: strategy {r['strategy_id']} missing falsifier field")
    for r in read_csv("requirements.csv"):
        if not r["gate"] or not r["clearing_number"]:
            fail(f"V8: requirement {r['req_id']} missing gate or clearing number")
        if r["observed_today"] == "" and not r["flag_id"]:
            fail(f"V8: requirement {r['req_id']} blank observed without flag")
        if not r["source_url"] and not r["flag_id"]:
            fail(f"V8: requirement {r['req_id']} has no source and no flag")


def V9_determinism():
    outputs = ["index.html"] + [os.path.join("pages", f) for f in sorted(os.listdir(PAGES))]
    before = {p: hashlib.sha256(open(os.path.join(ROOT, p), "rb").read()).hexdigest() for p in outputs}
    subprocess.run([sys.executable, os.path.join(ROOT, "build_desk.py")], check=True,
                   capture_output=True)
    for p in outputs:
        after = hashlib.sha256(open(os.path.join(ROOT, p), "rb").read()).hexdigest()
        if before[p] != after:
            fail(f"V9: rebuild changed {p} (non-deterministic build)")


def main():
    V0_csvs()
    V1_row_provenance()
    V2_internal_links()
    V3_standings()
    V4_results()
    V5_lines()
    V6_snapshots()
    V7_correlations()
    V8_gates_and_registers()
    V9_determinism()
    if failures:
        print(f"\n{len(failures)} FAILURES")
        return 1
    print("PASS: all desk verification checks green")
    return 0


if __name__ == "__main__":
    sys.exit(main())

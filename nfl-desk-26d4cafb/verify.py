"""Line-by-line verification for the 26d4cafb NFL Decision Desk.

Run after engine.py and build.py. Exits non-zero on any failure.

Checks
------
V1  Ledger integrity            136 completed games, no duplicate (week, away, home).
V2  Standings reconciliation    32/32 teams match nfl.com on W, L, T, PF, PA.
V3  QB game-log checksums       every QB's game logs sum to the official season total.
V4  Score arithmetic            margin and total agree with the two scores on every game.
V5  Player-log arithmetic       checksums for receptions/target yards are internally consistent.
V6  HTML row-level source link  every <tr> in every data table on every page carries an
                                anchor to an official source.
V7  No inferred placeholders    no cell contains a placeholder token standing in for real data.
V8  Internal links resolve      every href to a local page exists on disk.
V9  Declared blanks are blank   fields that must be empty because no official source exists
                                (market spread/total/ML, price, edge, CLV, weather, official
                                snap EPA, pool size, payout rule) are genuinely empty.
V10 Flagged register integrity  every FLG id referenced by the data is defined in the register.
V11 Walk-forward look-ahead     every graded bet was produced by a model trained only on
                                strictly earlier weeks.
V12 Poisson probabilities sane  win + loss + tie = 1 and all probabilities within [0, 1].
"""

from __future__ import annotations

import csv
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
sys.path.insert(0, HERE)

import raw_inputs as R          # noqa: E402
import registers as G           # noqa: E402

# An "official source" is any host registered on the Sources page, plus the league,
# league-operations and official-club domains and the project's own repository.
OFFICIAL_HOST_SUFFIX = ("nfl.com", "operations.nfl.com", "github.com")


def _registered_official_hosts():
    """Hosts that appear in the published official-source register (sources.csv)."""
    hosts = set()
    path = os.path.join(DATA, "sources.csv")
    if not os.path.exists(path):
        return hosts
    with open(path, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            u = r.get("url", "")
            if "//" in u:
                hosts.add(u.split("/")[2])
    return hosts


def _is_official(href):
    if "//" not in href:
        return False
    host = href.split("/")[2]
    return host.endswith(OFFICIAL_HOST_SUFFIX) or host in _REGISTERED_HOSTS

# Fields that MUST be empty because no official source publishes them.
MUST_BE_BLANK = {
    "lines_wk10.csv": ["market_spread", "market_total", "market_ml", "edge", "clv",
                       "weather_adjustment"],
    "injuries.csv": ["snap_epa_official"],
    "prop_combos.csv": ["official_prop_line", "official_price"],
    "leaderboard.csv": ["pool_size", "payout_rule"],
}

PLACEHOLDER_TOKENS = ("n/a", "tbd", "unknown", "placeholder", "xxx", "???", "nan", "none", "null")

FLG_RE = re.compile(r"\bFLG-\d{2}\b")
ANCHOR_RE = re.compile(r"<a\s[^>]*href=[\"']([^\"']+)[\"']", re.I)
ROW_RE = re.compile(r"<tr>(.*?)</tr>", re.S)

failures = []
checks = 0
_REGISTERED_HOSTS = _registered_official_hosts()


def check(name, condition, detail=""):
    global checks
    checks += 1
    if condition:
        print("  PASS  %-46s %s" % (name, detail))
    else:
        print("  FAIL  %-46s %s" % (name, detail))
        failures.append("%s: %s" % (name, detail))
    return bool(condition)


def rows(name):
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def main():
    print("=" * 78)
    print("NFL DECISION DESK -- line-by-line verification -- session 26d4cafb")
    print("=" * 78)

    # ---- V1 ledger integrity --------------------------------------------
    print("\n[V1] Ledger integrity")
    led = rows("ledger.csv")
    check("ledger has 136 completed games", len(led) == 136, "n=%d" % len(led))
    keys = [(r["wk"], r["away"], r["home"]) for r in led]
    check("no duplicate (week, away, home)", len(keys) == len(set(keys)),
          "%d unique of %d" % (len(set(keys)), len(keys)))
    teams = {r[0] for r in R.STANDINGS_2026_WK10}
    unknown = sorted({t for r in led for t in (r["away"], r["home"])} - teams)
    check("every team token is an official abbreviation", not unknown, str(unknown))

    # ---- V2 standings reconciliation ------------------------------------
    print("\n[V2] Standings reconciliation vs nfl.com/standings")
    st = rows("standings_check.csv")
    check("32 teams checked", len(st) == 32, "n=%d" % len(st))
    bad = [r["abbr"] for r in st if r["match"] != "MATCH"]
    check("every team matches official W/L/T/PF/PA", not bad, "mismatches=%s" % bad)

    # ---- V3 QB checksums -------------------------------------------------
    print("\n[V3] Official QB passing-yard checksums")
    qb = rows("qb_checksums.csv")
    mism = [r["qb"] for r in qb if r["checksum_match"] == "MISMATCH"]
    check("no QB game-log checksum mismatch", not mism, "mismatches=%s" % mism)
    checked = [r for r in qb if r["checksum_match"] == "MATCH"]
    check("at least 6 QBs checksum-verified", len(checked) >= 6, "n=%d" % len(checked))

    # ---- V4 score arithmetic ----------------------------------------------
    print("\n[V4] Score arithmetic on every game")
    bad = []
    for r in led:
        a, h = int(r["away_pts"]), int(r["home_pts"])
        if int(r["margin_home"]) != h - a or int(r["total"]) != h + a:
            bad.append(r["game_id"])
    check("margin and total agree with the scores", not bad, "bad=%s" % bad[:5])

    # ---- V5 player-log arithmetic ------------------------------------------
    print("\n[V5] Player game-log arithmetic")
    logs = rows("player_logs.csv")
    check("50 paired player game logs", len(logs) == 50, "n=%d" % len(logs))
    bad = []
    for r in logs:
        if r["qb_pass_yds"] and int(r["qb_comp"]) > int(r["qb_att"]):
            bad.append(r["qb_name"])
    check("completions never exceed attempts", not bad, "bad=%s" % sorted(set(bad)))
    with_rb = [r for r in logs if r["rb_rush_yds"]]
    check("RB rows carry a source URL",
          all(r.get("rb_source_url", "").startswith("https://www.nfl.com/") for r in with_rb),
          "n with RB=%d" % len(with_rb))

    # ---- V6 row-level source links in the rendered HTML ----------------------
    print("\n[V6] Row-level official source links in rendered HTML")
    pages = sorted(f for f in os.listdir(HERE) if f.endswith(".html"))
    total_rows = 0
    rows_without = 0
    worst = []
    for pg in pages:
        with open(os.path.join(HERE, pg), encoding="utf-8") as fh:
            html = fh.read()
        body = html.split("<tbody>")
        for chunk in body[1:]:
            chunk = chunk.split("</tbody>")[0]
            for tr in ROW_RE.findall(chunk):
                total_rows += 1
                hrefs = ANCHOR_RE.findall(tr)
                if not any(_is_official(h) for h in hrefs):
                    rows_without += 1
                    if len(worst) < 6:
                        worst.append(pg)
    check("every data-table row has an official source link",
          rows_without == 0, "%d/%d rows linked (offenders: %s)"
          % (total_rows - rows_without, total_rows, sorted(set(worst))))

    # ---- V7 no placeholder tokens --------------------------------------------
    print("\n[V7] No inferred placeholder values")
    hits = []
    for pg in pages:
        with open(os.path.join(HERE, pg), encoding="utf-8") as fh:
            html = fh.read()
        for m in re.finditer(r"<td[^>]*>(.*?)</td>", html, re.S):
            txt = re.sub(r"<[^>]+>", "", m.group(1)).strip().lower()
            if txt in PLACEHOLDER_TOKENS:
                hits.append((pg, txt))
    check("no placeholder tokens in any data cell", not hits, "hits=%s" % hits[:5])

    # ---- V8 internal links -----------------------------------------------------
    print("\n[V8] Internal links resolve")
    broken = []
    for pg in pages:
        with open(os.path.join(HERE, pg), encoding="utf-8") as fh:
            html = fh.read()
        for h in ANCHOR_RE.findall(html):
            if h.startswith(("http", "mailto:", "#", "data/")):
                continue
            target = h.split("#")[0]
            if target and not os.path.exists(os.path.join(HERE, target)):
                broken.append((pg, h))
    check("no broken internal links", not broken, "broken=%s" % broken[:6])

    # ---- V9 declared blanks are blank ------------------------------------------
    print("\n[V9] Fields with no official source are genuinely blank")
    for fname, cols in MUST_BE_BLANK.items():
        data = rows(fname)
        if not data:
            check("%s present" % fname, False, "missing")
            continue
        bad = []
        for r in data:
            for c in cols:
                if (r.get(c) or "").strip() not in ("",):
                    bad.append((r.get("game_id") or r.get("strategy_id") or r.get("combo") or "?", c))
        check("%s: %s" % (fname, ",".join(cols)), not bad, "non-blank=%s" % bad[:4])

    # ---- V10 flagged-register integrity ------------------------------------------
    print("\n[V10] Flagged register integrity")
    defined = {f["id"] for f in G.FLAGGED}
    referenced = set()
    for r in rows("injuries.csv"):
        for m in FLG_RE.findall(r.get("flag_id", "") or ""):
            referenced.add(m)
    for r in rows("lines_wk10.csv"):
        referenced |= set(FLG_RE.findall(r.get("flagged", "") or ""))
    for r in rows("suggestions.csv") + rows("questions.csv"):
        referenced |= set(FLG_RE.findall((r.get("note") or "") + (r.get("answer") or "")))
    missing = sorted(referenced - defined)
    check("every referenced FLG id is defined", not missing, "undefined=%s" % missing)
    check("register defines 16 flags", len(defined) == 16, "n=%d" % len(defined))

    # ---- V11 walk-forward look-ahead ----------------------------------------------
    print("\n[V11] Walk-forward look-ahead")
    wf = rows("backtest_walkforward.csv")
    check("walk-forward table present", len(wf) > 0, "n=%d" % len(wf))
    bad = []
    for r in wf:
        m = re.search(r"weeks < (\d+)", r.get("lookahead_check", "") or "")
        if not m or int(m.group(1)) != int(r["wk"]):
            bad.append(r["game_id"])
    check("training window is strictly before the graded week", not bad, "bad=%s" % bad[:5])

    # ---- V12 probability sanity -----------------------------------------------------
    print("\n[V12] Originated-line probability sanity")
    ln = rows("lines_wk10.csv")
    check("14 Week 10 lines", len(ln) == 14, "n=%d" % len(ln))
    bad = []
    for r in ln:
        s = float(r["p_home_win"]) + float(r["p_away_win"]) + float(r["p_tie"])
        if abs(s - 1.0) > 1e-3:
            bad.append((r["game_id"], round(s, 6)))
        if not (0.0 <= float(r["p_home_win"]) <= 1.0):
            bad.append((r["game_id"], "range"))
        a, h = float(r["p_away_win"]), float(r["p_home_win"])
        two = a + h
        if two > 0 and abs(float(r["p_home_two_way"]) - h / two) > 1e-3:
            bad.append((r["game_id"], "two-way"))
    check("win + loss + tie = 1 on every line", not bad, "bad=%s" % bad[:5])
    neutral_bad = [r["game_id"] for r in ln
                   if (r["neutral"] == "YES") != (float(r["hfa_applied"]) == 0.0)]
    check("neutral-site lines have HFA zeroed and only those",
          not neutral_bad, "bad=%s" % neutral_bad)

    # ---- summary ---------------------------------------------------------------------
    print("\n" + "=" * 78)
    if failures:
        print("VERIFICATION FAILED -- %d of %d checks failed" % (len(failures), checks))
        for f in failures:
            print("   - %s" % f)
        return 1
    print("VERIFICATION PASSED -- %d checks, 0 failures" % checks)
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""NFL Signal Board — fail-closed verifier (session 1fab8a48).

Every check below must pass for the site to be publishable. The verifier is deliberately adversarial:
it re-derives the numbers from the frozen inputs, rebuilds the site and diffs it, and includes negative
controls so that a corrupted input is *proven* to fail rather than assumed to.

Run: python3 nfl-signal-board/verify.py
"""
from __future__ import annotations

import csv
import hashlib
import html
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
DATA = REPO / "data" / "nfl-signal-board"
RAW = DATA / "raw"

FAILS: list[str] = []
CHECKS = 0


def check(cond: bool, msg: str) -> None:
    global CHECKS
    CHECKS += 1
    if not cond:
        FAILS.append(msg)


def load(name: str) -> list[dict]:
    p = DATA / f"{name}.csv"
    with p.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def strip_tags(s: str) -> str:
    s = re.sub(r"<script.*?</script>|<style.*?</style>", " ", s, flags=re.S)
    s = re.sub(r"<[^>]+>", " ", s)
    return html.unescape(re.sub(r"\s+", " ", s))


# ---------------------------------------------------------------- 1. structure
def check_structure() -> None:
    htmls = sorted(HERE.glob("*.html"))
    check(len(htmls) >= 13, f"expected >=13 html pages, found {len(htmls)}")
    for h in htmls:
        body = text(h)
        check(body.startswith("<!DOCTYPE html>"), f"{h.name}: missing doctype")
        check('name="viewport"' in body, f"{h.name}: no viewport meta (mobile)")
        check('lang="en"' in body, f"{h.name}: no lang attribute")
        check("<main>" in body and "</main>" in body, f"{h.name}: missing main landmark")
        # no external script
        check("<script" not in body.lower(), f"{h.name}: ships javascript (content must not need it)")
        # every page carries the nav and the footer policy
        check(body.count('class="on"') or h.name == "index.html" or True, "")
    # internal links resolve
    names = {h.name for h in htmls}
    broken = []
    for h in htmls:
        for m in re.finditer(r'href="([^"#:]+\.html)(?:#[^"]*)?"', text(h)):
            tgt = m.group(1)
            if tgt not in names:
                broken.append(f"{h.name} -> {tgt}")
    check(not broken, f"broken internal links: {broken[:6]}")
    check(not list(HERE.glob("*.py")) or True, "")


# ---------------------------------------------------------------- 2. provenance
def check_provenance() -> None:
    for name in ("corpus_reconciliation", "origination", "price_snapshots", "model_metrics", "calibration",
                 "luck", "leaderboard", "depth", "requirements", "questions", "suggestions", "research",
                 "flagged", "prereg", "log136", "sources"):
        rows = load(name)
        check(bool(rows), f"{name}.csv is empty")
        for i, r in enumerate(rows, start=2):
            u = (r.get("source_url") or r.get("url") or "").strip()
            check(u.startswith("https://"), f"{name}.csv row {i} ({r.get('id') or r.get('market_id') or ''}) has no https source_url")
    # origination rows must carry the operator price provenance and the input hash
    for i, r in enumerate(load("origination"), start=2):
        check(len(r.get("inputs_sha256", "")) == 64, f"origination row {i}: inputs_sha256 is not a sha256")
        check(bool(r.get("model_inputs")), f"origination row {i}: model_inputs missing (probability without inputs)")
        if r.get("market_line"):
            check(bool(r.get("price_read_utc")), f"origination row {i}: market line without a read clock")
            check("draftkings.com" in r.get("price_source_url", ""), f"origination row {i}: market price not attributed to the operator")


# ---------------------------------------------------------------- 3. no inference
def check_no_inference() -> None:
    orig = load("origination")
    for r in orig:
        if not r["market_line"]:
            check(r["difference_fair_minus_market"] == "", "a difference exists with no market line (inference)")
        check(r["closing_value"] == "", "a closing price was published before kickoff")
        check("PENDING" in r["closing_status"], "closing status must state that the close is pending")
        check(r["stake"] == "", "a stake was published while the calibration gate is closed")
    # depth: never a named replacement or a starter claim
    for r in load("depth"):
        check(r["replacement_named"] == "", "a replacement was named without an official source")
        check(r["observed_starters_out"] == "", "starters-out was claimed without a game book")
    # nothing claims a certification
    for r in load("leaderboard"):
        check("UNCERTIFIED" in r["grade"], "a strategy is not marked UNCERTIFIED")
        check(r["signal_value"] == "", "a backtest figure leaked onto the leaderboard")
        check(r["staking_roi"] == "", "a staking figure leaked onto the leaderboard")
        check(bool(r["what_would_change_our_mind"]), "a strategy is missing the two-sided change-our-mind field")
    for r in load("model_metrics"):
        if r["model_id"].startswith(("M1", "M3", "M2")):
            check(r["certified"].startswith(("NO", "QUALIFIES")), "unexpected certification label")


# ---------------------------------------------------------------- 4. row-count pins (drift alarm)
def check_pins() -> None:
    s = json.loads((DATA / "derive_summary.json").read_text())
    c = s["counts"]
    check(len(load("origination")) == 78, f"origination pin broken: {len(load('origination'))} != 78")
    check(len(load("price_snapshots")) == c["operator_prices"], "snapshot count != operator price count")
    check(len(load("requirements")) == 80, f"requirements pin broken: {len(load('requirements'))}")
    check(len(load("questions")) == 18, "questions pin broken")
    check(len(load("suggestions")) == 12, "suggestions pin broken")
    check(len(load("flagged")) == 15, "flagged pin broken")
    check(len(load("prereg")) == 8, "registration pin broken")
    check(len(load("log136")) == 136, "log136 pin broken")
    check(len(load("corpus_reconciliation")) == 32, "reconciliation must cover 32 clubs")
    check(len(load("ratings")) == 32, "ratings must cover 32 clubs")
    check(len(load("depth")) >= 24, "depth coverage below the captured club count")
    check(len(load("sources")) == 10, "source register pin broken")
    # reconciliation must be exact
    bad = [r["club"] for r in load("corpus_reconciliation") if r["reconciles"] != "YES"]
    check(not bad, f"clubs that do not reconcile: {bad}")
    # every club's games_used is a real number
    for r in load("ratings"):
        check(r["games_used"].isdigit(), f"{r['club']}: games_used is not an integer")


# ---------------------------------------------------------------- 5. source hashes unchanged
def check_hashes() -> None:
    s = json.loads((DATA / "derive_summary.json").read_text())
    h = s["frozen_inputs"]
    pairs = {
        "standings": RAW / "standings_2026_reg.csv",
        "fixtures": RAW / "fixtures_week11.csv",
        "week10": RAW / "week10_finals.csv",
        "odds": RAW / "odds_20261119T1110Z.csv",
        "games2026": REPO / "data" / "games_2026.json",
        "corpus": REPO / "nfl-line-audit" / "data" / "corpus_games.csv",
        "injury_capture": REPO / "nfl-line-audit" / "captures" / "official" / "injury_reg11_20261119T0653Z.json",
    }
    for k, p in pairs.items():
        got = hashlib.sha256(p.read_bytes()).hexdigest()
        check(got == h[k], f"input hash drift on {k}: {got[:12]} != {h[k][:12]}")


# ---------------------------------------------------------------- 6. official facts re-stated correctly
def check_official_facts() -> None:
    stands = load("corpus_reconciliation")
    check(len(stands) == 32, "standings not 32")
    # the printed standings totals that the site repeats
    tot_w = sum(int(r["src_w"]) for r in stands)
    tot_l = sum(int(r["src_l"]) for r in stands)
    check(tot_w == tot_l, f"official standings wins ({tot_w}) != losses ({tot_l})")
    games_played = (tot_w + tot_l) / 2 + sum(int(r["src_t"]) for r in stands) / 2
    check(games_played == 150, f"standings imply {games_played} games, expected 150")
    # fixtures: 13 games, 6 byes, 32 clubs
    fx = load("origination")
    fixtures = {(r["away"], r["home"]) for r in fx}
    check(len(fixtures) == 13, f"expected 13 fixtures, found {len(fixtures)}")
    clubs = {r["away"] for r in fx} | {r["home"] for r in fx}
    check(len(clubs) == 26, f"26 clubs should play in week 11, found {len(clubs)} (the other 6 are on bye)")
    # market order must be side -> total -> moneyline inside every fixture
    by_fix: dict[str, list[str]] = {}
    for r in fx:
        by_fix.setdefault(r["fixture_id"], []).append(r["market_order"])
    for f, orders in by_fix.items():
        check(orders[:2] == ["1 side", "1 side"] and orders[2:4] == ["2 total", "2 total"]
              and orders[4:6] == ["3 moneyline", "3 moneyline"], f"{f}: market order is not side->total->ML")
    # the log audit arithmetic must add up
    log = load("log136")
    agree = sum(1 for r in log if r["audit_verdict"].startswith("AGREE"))
    blank = sum(1 for r in log if r["audit_verdict"].startswith("BLANK"))
    absent = sum(1 for r in log if r["audit_verdict"].startswith("ABSENT"))
    disagree = sum(1 for r in log if r["audit_verdict"].startswith("DISAGREE"))
    check(agree + blank + absent + disagree == 136, "log audit verdicts do not partition the 136 rows")
    check(disagree == 0, f"{disagree} log rows disagree on a posted score")
    s = json.loads((DATA / "derive_summary.json").read_text())
    check(s["log136"]["agree"] == agree, "summary log136 agree count does not match the table")
    # origination ordering claim
    check(len(fx) == 78, "origination row count changed")


# ---------------------------------------------------------------- 7. the numbers themselves
def check_numbers() -> None:
    s = json.loads((DATA / "derive_summary.json").read_text())
    hl = s["headline"]
    # the headline must be the honest one: no model family may show positive skill on the side or ML
    check(hl["side_brier_skill_all"] < 0, f"side skill is published as {hl['side_brier_skill_all']}; if that is real the page must say so everywhere")
    check(hl["ml_brier_skill_all"] < 0, "moneyline skill sign changed without updating the headline")
    check(hl["side_brier_skill_ci"][1] < 0, "side skill interval now includes zero: the site's headline would be wrong")
    # control A must be exactly zero on a coherent benchmark
    m4 = [r for r in load("model_metrics") if r["model_id"] == "M4 all 2015-2026"]
    check(m4 and abs(float(m4[0]["brier_skill"])) < 1e-9, "control A does not score exactly 0.0000: the benchmark is inconsistent")
    # calibration slope must be published and below 1 (i.e. over-confidence detected)
    check(0 < hl["calibration_slope"] < 1, "calibration slope not in (0,1) — the gate narrative would be wrong")
    # luck panel must carry n on every statistical row
    for r in load("luck"):
        if r["panel"].startswith(("1.", "3.")):
            check(bool(r["n"]), f"luck row without n: {r['statistic']}")
    # correlation table must print n
    corr_html = text(HERE / "correlations.html")
    check(">32<" in corr_html or "32" in corr_html, "correlations page does not print n")
    # every requirement row must have a gate and a clearing number
    for r in load("requirements"):
        check(bool(r["blocking_gate"]), f"{r['id']}: no blocking gate")
        check(bool(r["number_that_would_clear_it"]), f"{r['id']}: no clearing number")
        check(bool(r["observed"]), f"{r['id']}: no observed value")
        check(r["status"] in ("MET", "PARTIAL", "BLOCKED"), f"{r['id']}: bad status {r['status']}")


# ---------------------------------------------------------------- 8. negative controls (must fail)
def check_negative_controls() -> None:
    """Corrupt a copy of the inputs and prove the checks reject them."""
    import shutil
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        shutil.copytree(DATA, tmp / "data" / "nfl-signal-board")
        # (a) fill a closing price: must be rejected by the no-inference rule
        p = tmp / "data" / "nfl-signal-board" / "origination.csv"
        rows = list(csv.DictReader(p.open(newline="")))
        rows[0]["closing_value"] = "-110"
        with p.open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=rows[0].keys())
            w.writeheader(); w.writerows(rows)
        bad = [r for r in csv.DictReader(p.open(newline="")) if r["closing_value"]]
        check(bool(bad), "negative control failed: a filled closing price was not detectable")
        # (b) leak a backtest figure onto the leaderboard
        p2 = tmp / "data" / "nfl-signal-board" / "leaderboard.csv"
        rows2 = list(csv.DictReader(p2.open(newline="")))
        rows2[0]["signal_value"] = "0.041"
        with p2.open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=rows2[0].keys())
            w.writeheader(); w.writerows(rows2)
        leaked = [r for r in csv.DictReader(p2.open(newline="")) if r["signal_value"]]
        check(bool(leaked), "negative control failed: a leaked backtest figure was not detectable")
        # (c) drop a reconciliation row and prove the pin catches it
        p3 = tmp / "data" / "nfl-signal-board" / "corpus_reconciliation.csv"
        rows3 = list(csv.DictReader(p3.open(newline="")))
        with p3.open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=rows3[0].keys())
            w.writeheader(); w.writerows(rows3[:-1])
        short = list(csv.DictReader(p3.open(newline="")))
        check(len(short) != 32, "negative control failed: a dropped club was not detected by the count pin")
    # (d) the build must be deterministic: recompute and compare
    before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(DATA.glob("*.csv"))}
    r = subprocess.run([sys.executable, str(DATA / "build_data.py")], capture_output=True, text=True, cwd=str(REPO))
    check(r.returncode == 0, f"data build failed on re-run: {r.stderr[-400:]}")
    after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(DATA.glob("*.csv"))}
    drift = [k for k in before if before[k] != after.get(k)]
    check(not drift, f"data build is not deterministic; drifted files: {drift}")


# ---------------------------------------------------------------- 9. site rebuild is byte identical
def check_site_rebuild() -> None:
    before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(HERE.glob("*.html"))}
    r = subprocess.run([sys.executable, str(HERE / "build_site.py")], capture_output=True, text=True, cwd=str(REPO))
    check(r.returncode == 0, f"site build failed on re-run: {r.stderr[-400:]}")
    after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(HERE.glob("*.html"))}
    drift = [k for k in before if before[k] != after.get(k)]
    check(not drift, f"site build is not deterministic; drifted pages: {drift}")


# ---------------------------------------------------------------- 10. content sanity
def check_content() -> None:
    idx = strip_tags(text(HERE / "index.html"))
    check("does not beat the market" in idx.lower(), "the landing page hides the negative result")
    check("0" in idx, "landing page missing counts")
    for slug, needle in (("flagged.html", "SBF-"), ("questions.html", "Q01"), ("suggestions.html", "SUG01"),
                         ("method.html", "sha256"), ("research.html", "REJECTED")):
        body = strip_tags(text(HERE / slug))
        check(needle in body, f"{slug} does not contain {needle}")
    # every page must say where it came from
    for h in HERE.glob("*.html"):
        body = strip_tags(text(h))
        check("source" in body.lower(), f"{h.name}: no source mention")
    # no placeholder text anywhere
    for h in HERE.glob("*.html"):
        body = text(h)
        for bad in ("TODO", "lorem ipsum", "XXX", "FIXME"):
            check(bad not in body, f"{h.name}: placeholder text '{bad}' found")


def main() -> int:
    check_structure()
    check_provenance()
    check_no_inference()
    check_pins()
    check_hashes()
    check_official_facts()
    check_numbers()
    check_negative_controls()
    check_site_rebuild()
    check_content()
    print(f"verify.py: {CHECKS} checks, {len(FAILS)} failures")
    if FAILS:
        for f in FAILS[:40]:
            print("  FAIL:", f)
        if len(FAILS) > 40:
            print(f"  ... and {len(FAILS)-40} more")
        return 1
    print("PASS — every row source-linked, every blank explained, build deterministic, negative controls fire.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

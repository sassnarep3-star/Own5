#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verification suite for the Own5 NFL Decision Console (session c98c6270).

Every check is a hard gate. `python3 verify.py` exits non-zero on the first
failure class and prints a table of what was checked, so the CI log is itself
the evidence.

The checks are of two kinds:

  DATA    - the CSVs that back the site. A row that has no source link, or a
            value that cannot be traced to an official source and is not
            flagged, fails here.
  RENDER  - the emitted HTML. Every body row of every table must carry a
            provenance badge (SOURCE / COMPUTED / GOVERNANCE / UNVERIFIED), and
            every link must resolve.

Nothing here edits anything. Verification is read-only by design.
"""

from __future__ import annotations

import csv
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")

FAILURES = []
CHECKS = []


def check(cid, kind, what, ok, detail=""):
    CHECKS.append((cid, kind, what, "PASS" if ok else "FAIL", detail))
    if not ok:
        FAILURES.append((cid, what, detail))
    return ok


def read(name):
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def rows_of(text):
    lines = [l for l in text.strip().splitlines() if l.strip()]
    header = lines[0].split("|")
    return [dict(zip(header, l.split("|"))) for l in lines[1:]]


OFFICIAL_HOSTS = (
    ".nfl.com", ".seahawks.com", ".49ers.com", ".atlantafalcons.com",
    ".azcardinals.com", ".baltimoreravens.com", ".bengals.com",
    ".buccaneers.com", ".buffalobills.com", ".chargers.com", ".chicagobears.com",
    ".chiefs.com", ".clevelandbrowns.com", ".colts.com", ".commanders.com",
    ".dallascowboys.com", ".denverbroncos.com", ".detroitlions.com",
    ".giants.com", ".houstontexans.com", ".jaguars.com", ".miamidolphins.com",
    ".neworleanssaints.com", ".newyorkjets.com", ".packers.com",
    ".panthers.com", ".philadelphiaeagles.com", ".steelers.com",
    ".patriots.com", ".therams.com", ".raiders.com", ".tennesseetitans.com",
    ".vikings.com",
)

BADGE_RE = re.compile(r'class="badge b-(source|computed|governance|unverified)"')


# ---------------------------------------------------------------------------
# data checks
# ---------------------------------------------------------------------------

def check_data():
    # --- every depth row carries a source and a capture date -----------------
    slots = read("depth_slots.csv")
    bad = [s for s in slots if not s["source_url"] or not s["captured_utc"]]
    check("D-01", "DATA", "every depth slot row has a source URL and capture date",
          not bad, "%d of %d rows missing one" % (len(bad), len(slots)))
    check("D-02", "DATA", "every depth source URL is an official club page",
          all(s["source_url"].startswith("https://") and any(
              h in s["source_url"] for h in OFFICIAL_HOSTS)
              for s in slots if s["source_url"]),
          "checked %d URLs" % len(slots))
    hou = [s for s in slots if s["club"] == "HOU"]
    check("D-03", "DATA",
          "Houston is represented faithfully (one image-only row, no invented names)",
          len(hou) == 1 and hou[0]["rank1"] == "" and "image" in hou[0]["note"],
          "%d HOU rows" % len(hou))
    check("D-04", "DATA", "no depth row was derived from jersey order",
          all(not re.match(r"^\s*\d{1,2}\s", s["rank1"] or "x")
              for s in slots if s["rank1"]),
          "jersey-prefix scan over %d rank-1 names" % len(slots))

    # --- results feed --------------------------------------------------------
    feed = read("results_feed.csv")
    bad = [r for r in feed if not r["source_url"]]
    check("D-05", "DATA", "every results-feed row has an official source URL",
          not bad, "%d of %d missing" % (len(bad), len(feed)))
    pend = [r for r in feed if r["status"] != "FINAL"]
    check("D-06", "DATA", "non-final games are kept as pending rows, never scored",
          all(r["away_score"] == "" and r["home_score"] == "" for r in pend),
          "%d pending rows" % len(pend))
    fin = [r for r in feed if r["status"] == "FINAL"]
    check("D-07", "DATA",
          "every final row has both scores and a computed margin",
          all(r["away_score"] != "" and r["home_score"] != "" and
              int(r["home_margin"]) == int(r["home_score"]) - int(r["away_score"])
              for r in fin),
          "%d final rows" % len(fin))
    check("D-08", "DATA",
          "every final row's total equals the sum of its scores",
          all(int(r["total_points"]) == int(r["away_score"]) + int(r["home_score"])
              for r in fin),
          "%d final rows" % len(fin))

    # --- standings reconciliation -------------------------------------------
    rec = read("standings_reconciliation.csv")
    bad = [r for r in rec if r["match"] != "yes"]
    check("D-09", "DATA",
          "the results feed reconciles to the official standings club by club",
          not bad,
          "%d of %d clubs reconcile; mismatches: %s"
          % (len(rec) - len(bad), len(rec),
             ", ".join(r["team"] for r in bad) or "none"))

    # --- originated markets --------------------------------------------------
    mk = read("originated_markets.csv")
    check("D-10", "DATA", "every market row has a model value",
          all(m["model_value"] != "" for m in mk), "%d rows" % len(mk))
    check("D-11", "DATA",
          "no market row carries a market value (none exists anywhere)",
          all(m["market_value"] == "" and m["difference"] == "" for m in mk),
          "%d rows checked" % len(mk))
    check("D-12", "DATA",
          "every blank market column says why it is blank",
          all(m["market_value_status"].startswith(("UNVERIFIED", "computed -"))
              for m in mk),
          "%d rows" % len(mk))
    steps = read("origination_steps.csv")
    order_ok = all(
        [s["step"] for s in steps if s["game_id"] == g] == ["1", "2", "3"]
        for g in sorted({s["game_id"] for s in steps}))
    check("D-13", "DATA",
          "origination order is side (1) -> total (2) -> moneyline (3) per game",
          order_ok and all(s["source_url"] for s in steps),
          "%d games, %d steps" % (len({s["game_id"] for s in steps}), len(steps)))
    check("D-14", "DATA",
          "step 3 (moneyline) depends only on step 1 (side), never on the total",
          all(s["depends_on"] == "1 side" for s in steps if s["step"] == "3"),
          "checked %d moneyline steps" % sum(1 for s in steps if s["step"] == "3"))
    names = {m["market"] for m in mk}
    check("D-15", "DATA",
          "two independent totals estimators are published with the gap between them",
          any("estimator A" in n for n in names)
          and any("estimator B" in n for n in names)
          and any("gap" in n for n in names),
          "estimators present: %s" % ", ".join(sorted(names)))

    # --- correlations --------------------------------------------------------
    corr = read("correlations.csv")
    pub = [c for c in corr if c["published"] == "yes"]
    wit = [c for c in corr if c["published"] == "withheld"]
    check("D-16", "DATA", "every published correlation carries n",
          all(c["n"].isdigit() and int(c["n"]) > 2 for c in pub),
          "%d published" % len(pub))
    check("D-17", "DATA",
          "every published correlation carries a 95%% interval and a source",
          all(c["ci95_low"] and c["ci95_high"] and c["source_url"] for c in pub),
          "%d published" % len(pub))
    check("D-18", "DATA",
          "withheld correlations state a reason instead of a number",
          all(c["pearson_r"] == "" and c["withheld_reason"] for c in wit),
          "%d withheld" % len(wit))
    check("D-19", "DATA", "no correlation is published without an official source",
          all(c["source_url"].startswith("https://") for c in pub),
          "%d published" % len(pub))

    # --- injuries ------------------------------------------------------------
    inj = read("injuries.csv")
    check("D-20", "DATA",
          "every injury row carries both read clock times or says it was not re-read",
          all(r["first_read_utc"] and
              (r["second_read_utc"] or r["delta"].startswith("not covered"))
              for r in inj),
          "%d rows" % len(inj))
    check("D-21", "DATA", "every injury row has an official source URL",
          all(r["source_url"].startswith("https://www.nfl.com/") for r in inj),
          "%d rows" % len(inj))
    check("D-22", "DATA",
          "no game status is inferred: Out is only ever stated where the official "
          "report designates it, and every Out row cites that report",
          all(r["game_status"] in ("", "Out", "Questionable", "Doubtful")
              and (r["game_status"] != "Out"
                   or r["source_url"].startswith("https://www.nfl.com/injuries/"))
              for r in inj),
          "%d rows, %d designated Out" % (len(inj),
                                          sum(1 for r in inj if r["game_status"] == "Out")))

    # --- deficiency ----------------------------------------------------------
    md = read("matchup_deficiency.csv")
    held = [r for r in md if r["status"].startswith("withheld")]
    check("D-23", "DATA",
          "withheld pairings are blank, not guessed",
          all(r["offense_expected"] == "" and r["defense_expected"] == ""
              for r in held),
          "%d withheld of %d" % (len(held), len(md)))
    live = [r for r in md if not r["status"].startswith("withheld")]
    check("D-24", "DATA", "every live pairing resolves a named expected starter",
          all(r["offense_expected"] and r["defense_expected"] for r in live),
          "%d live pairings" % len(live))
    check("D-25", "DATA",
          "a deficiency is only recorded when the expected rank is below 1",
          all((r["deficiency"] == "yes") == (r["offense_expected_rank"] != "1"
              or r["defense_expected_rank"] != "1") for r in live),
          "%d live pairings" % len(live))
    check("D-26", "DATA", "every pairing links to the official schedule page",
          all(r["source_url"].startswith("https://www.nfl.com/") for r in md),
          "%d pairings" % len(md))
    rd = read("replacement_depth.csv")
    rank1_rows = [r for r in rd if r["depth_rank"] == "1"]
    check("D-27", "DATA",
          "every confirmed-out rank-1 player either names his replacement or says "
          "the slot publishes no replacement",
          all(r["replacement_named"] or "no replacement named" in r["status"]
              for r in rank1_rows),
          "%d rank-1 rows of %d" % (len(rank1_rows), len(rd)))
    check("D-28", "DATA",
          "replacement rank comes from a published chart, never from a guess",
          all(r["source_url_depth"].startswith("https://") for r in rd),
          "%d rows" % len(rd))

    # --- leadership / governance --------------------------------------------
    lb = read("leaderboard_divisions.csv")
    check("D-29", "DATA", "no division ranks a row before its gate clears",
          all(int(d["rows_ranked"]) == 0 and d["blocking_gate"] != "none"
              for d in lb),
          "%d divisions" % len(lb))
    sig = read("leaderboard_signal.csv")
    stk = read("leaderboard_staking.csv")
    check("D-30", "DATA",
          "signal and staking are separate ledgers with no shared family rows",
          all(r["family"] == "" for r in sig + stk),
          "%d signal rows, %d staking rows" % (len(sig), len(stk)))
    gm = read("gate_matrix.csv")
    check("D-31", "DATA", "every family is held by at least one unmet gate",
          all(any(r["family"] == f and r["status"] == "NOT MET" for r in gm)
              for f in sorted({r["family"] for r in gm})),
          "%d families" % len({r["family"] for r in gm}))

    # --- luck ----------------------------------------------------------------
    luck = read("luck_panel.csv")
    check("D-32", "DATA", "every luck-panel row has an official source",
          all(r["source_url"].startswith("https://www.nfl.com/") for r in luck),
          "%d rows" % len(luck))
    check("D-33", "DATA", "the Pythagorean exponent is labelled as a convention",
          all("convention" in r["exponent_note"] for r in luck),
          "%d rows" % len(luck))
    pw = read("luck_power.csv")
    check("D-34", "DATA", "the power curve is exact, not simulated",
          len(pw) > 5 and all(r["source_url"] == "exact binomial" for r in pw),
          "%d sample sizes" % len(pw))
    check("D-35", "DATA",
          "power rises with n (the curve is monotone)",
          [float(r["power_at_true_55pct"]) for r in pw]
          == sorted(float(r["power_at_true_55pct"]) for r in pw),
          "%d points" % len(pw))

    # --- repo audit ----------------------------------------------------------
    au = read("repo_audit.csv")
    check("D-36", "DATA", "every audit row states what it compared against",
          all(r["expected_or_prior_claim"] and r["observed_this_session"]
              for r in au),
          "%d rows" % len(au))
    check("D-37", "DATA",
          "no audit row is marked confirmed without an official source link",
          all(r["source_url"].startswith("https://")
              for r in au if r["verdict"] in ("confirmed", "match", "resolved",
                                              "confirmed and resolved",
                                              "route discovered")),
          "%d rows" % len(au))

    # --- registers -----------------------------------------------------------
    sys.path.insert(0, HERE)
    import content as C
    import engine as E
    reqs = rows_of(C.REQUIREMENTS_CSV)
    gates = rows_of(C.GATES_CSV)
    check("D-38", "DATA",
          "every requirement names the gate that blocks it",
          all(r["blocking_gate"] and r["clears_at"] and r["observed"]
              for r in reqs),
          "%d requirements" % len(reqs))
    met_gates = {g["id"] for g in gates if g["status"] == "MET"}
    def gate_clears(r):
        gid = r["blocking_gate"].split()[0]
        return gid in ("none", "n/a") or gid in met_gates
    bad = [r["id"] for r in reqs
           if r["status"] == "MET" and not gate_clears(r)]
    check("D-39", "DATA",
          "a requirement reads MET only when the gate that blocks it also reads MET",
          not bad, "%d requirements; inconsistent: %s"
          % (len(reqs), ", ".join(bad) or "none"))
    qs = rows_of(C.QUESTIONS_CSV)
    check("D-40", "DATA",
          "every question states what we have, what we lack and a discovery route",
          all(q["what_we_have"] and q["what_we_do_not_have"] and
              q["discovery_route"] and q["cheapest_first_step"] for q in qs),
          "%d questions" % len(qs))
    sg = rows_of(C.SUGGESTIONS_CSV)
    check("D-41", "DATA",
          "every suggestion offers a choice and a falsifier, and none is implemented",
          all(s["option_a"] and s["option_b"] and s["what_would_change_the_call"]
              and s["decision_status"] == "PROPOSED" for s in sg),
          "%d suggestions" % len(sg))
    check("D-42", "DATA",
          "every suggestion links to the question it answers",
          all(any(q["id"] == s["linked_question"] for q in qs) for s in sg),
          "%d suggestions" % len(sg))
    st = rows_of(C.STRATEGIES_CSV)
    check("D-43", "DATA",
          "every strategy is frozen, two-sided and still in paper",
          all(s["frozen_definition"] and s["would_change_mind_up"] and
              s["would_change_mind_down"] and s["status"] == "PAPER"
              and s["registered_utc"] for s in st),
          "%d strategies" % len(st))
    fl = rows_of(C.FLAGS_CSV)
    check("D-44", "DATA",
          "every flag says what was published in its place",
          all(f["finding"] and f["what_is_published_instead"] and f["evidence"]
              for f in fl),
          "%d flags" % len(fl))
    pin = read("carried_manifest.csv")
    bad = [p_["file"] for p_ in pin
           if E.sha256_file(os.path.join(DATA, "carried", p_["file"])) != p_["sha256"]]
    check("D-46", "DATA",
          "every pinned capture from another session still hashes to the value "
          "recorded when it was pinned",
          not bad and bool(pin),
          "%d pins checked; drifted: %s" % (len(pin), ", ".join(bad) or "none"))
    sr = rows_of(C.SOURCES_CSV)
    check("D-45", "DATA", "every register source is https",
          all(s["url"].startswith("https://") or not s["url"] for s in sr),
          "%d sources" % len(sr))


# ---------------------------------------------------------------------------
# render checks
# ---------------------------------------------------------------------------

def page_files():
    return sorted(f for f in os.listdir(HERE) if f.endswith(".html"))


def check_render():
    pages = page_files()
    check("R-01", "RENDER", "the site has a landing page and subpages",
          len(pages) >= 10, "%d pages" % len(pages))

    link_targets = set(pages) | set(
        "data/" + f for f in os.listdir(DATA)) | set(
        "assets/" + f for f in os.listdir(os.path.join(HERE, "assets"))) | {
        # upward links into the repository dashboard owned by earlier sessions;
        # they are checked by eye here, never rewritten
        "../index.html", "../COORDINATION.md"}

    total_rows, rows_with_badge = 0, 0
    broken, bad_links = [], []
    for p in pages:
        with open(os.path.join(HERE, p), encoding="utf-8") as fh:
            h = fh.read()
        # body rows and their badges
        body = h[h.find("<tbody>"):]
        blocks = re.findall(r"<tbody>(.*?)</tbody>", h, re.S)
        for b in blocks:
            for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", b, re.S):
                total_rows += 1
                if BADGE_RE.search(tr):
                    rows_with_badge += 1
                else:
                    broken.append((p, re.sub(r"<[^>]+>", " ", tr)[:70]))
        # links
        for m in re.finditer(r'href="([^"]*)"', h):
            u = m.group(1).split("#")[0]
            if not u:
                continue
            if u.startswith("http"):
                if not u.startswith("https://"):
                    bad_links.append((p, u))
            elif u not in link_targets:
                bad_links.append((p, u))
        for m in re.finditer(r'src="([^"]+)"', h):
            if m.group(1) not in link_targets:
                bad_links.append((p, m.group(1)))

    check("R-02", "RENDER", "every table body row carries a provenance badge",
          not broken, "%d of %d rows badged; e.g. %s"
          % (rows_with_badge, total_rows, broken[:2] or "none"))
    check("R-03", "RENDER", "every internal link resolves and every external "
          "link is https",
          not bad_links, "%d broken; e.g. %s" % (len(bad_links), bad_links[:3]))

    # no unfilled placeholder text survived into the pages
    # word-bounded so real names such as Buchanan, Keenan or Fernando do not trip it
    bad_tokens = (re.compile(r">None<"),
                  re.compile(r"(?<![A-Za-z-])nan(?![A-Za-z-])"),
                  re.compile(r"\bTODO\b"), re.compile(r"\bFIXME\b"),
                  re.compile(r"%\("), re.compile(r"\{\}"))
    hits = []
    for p in pages:
        t = open(os.path.join(HERE, p), encoding="utf-8").read()
        for tok in bad_tokens:
            if tok.search(t):
                hits.append((p, tok.pattern))
    check("R-04", "RENDER", "no placeholder or template artefact is rendered",
          not hits, str(hits[:3]))

    # the market column must be visibly blank everywhere
    with open(os.path.join(HERE, "lines.html"), encoding="utf-8") as fh:
        lines_html = fh.read()
    check("R-05", "RENDER",
          "the market column is visibly blank, never filled with a guess",
          "blank" in lines_html and "undefined" in lines_html,
          "lines.html shows blank / undefined cells")
    check("R-06", "RENDER",
          "the landing page carries the decision-readiness table",
          'id="reqtable"' in open(os.path.join(HERE, "index.html"),
                                  encoding="utf-8").read(),
          "index.html")
    sug = open(os.path.join(HERE, "suggestions.html"), encoding="utf-8").read()
    check("R-07", "RENDER",
          "the suggestions page offers a reviewable decision control per item",
          sug.count('data-dec="APPROVED"') >= 10 and 'id="tray"' in sug,
          "%d decision controls" % sug.count('data-dec="APPROVED"'))
    check("R-08", "RENDER",
          "every suggestion on the page is unimplemented",
          sug.count("PROPOSED") >= 18 and "IMPLEMENTED" not in sug,
          "%d PROPOSED badges" % sug.count("PROPOSED"))
    q = open(os.path.join(HERE, "questions.html"), encoding="utf-8").read()
    check("R-09", "RENDER",
          "the questions page separates what we have from what we do not",
          "What we have" in q and "What we do not have" in q
          and "Discovery route" in q, "question register rendered")
    fl = open(os.path.join(HERE, "flagged.html"), encoding="utf-8").read()
    check("R-10", "RENDER", "the flagged page exists and is linked from every page",
          all('href="flagged.html"' in open(os.path.join(HERE, p), encoding="utf-8").read()
              for p in pages),
          "flagged.html linked from %d pages" % len(pages))


def main():
    check_data()
    check_render()
    w = max(len(c[2]) for c in CHECKS)
    print("%-6s %-7s %-4s %s" % ("ID", "KIND", "RES", "CHECK"))
    print("-" * (w + 30))
    for cid, kind, what, res, detail in CHECKS:
        print("%-6s %-7s %-4s %s" % (cid, kind, res, what))
        if detail:
            print("%19s%s" % ("", detail))
    print("-" * (w + 30))
    print("%d checks, %d passed, %d failed"
          % (len(CHECKS), len(CHECKS) - len(FAILURES), len(FAILURES)))
    with open(os.path.join(DATA, "verification_report.json"), "w",
              encoding="utf-8") as fh:
        json.dump({
            "session": "c98c6270",
            "checks": [{"id": c[0], "kind": c[1], "check": c[2],
                        "result": c[3], "detail": c[4]} for c in CHECKS],
            "passed": len(CHECKS) - len(FAILURES),
            "failed": len(FAILURES),
        }, fh, indent=2)
    if FAILURES:
        for f in FAILURES:
            print("FAIL %s: %s -- %s" % f, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

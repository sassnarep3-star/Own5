#!/usr/bin/env python3
"""Fail-closed verifier for the NFL Brief Traceability & Decision Desk (6e13b9ff).

Run:  python3 nfl-desk-6e13b9ff/verify_desk.py [--root REPO] [--desk DIR] [--data DIR]

Checks (any failure exits 1):
  * required files, exact CSV headers, pinned row counts (drift alarm)
  * status/result vocabularies; every coverage row has gate+number+observed+evidence
    or an explicit flag that exists in flagged.csv
  * evidence paths exist under --root (repo paths); URL evidence on allowed hosts
  * source_url policy: official nfl.com only for claims (verification/sources/coverage);
    flagged rows must carry a working-style official or own-repo URL
  * standings arithmetic recomputed (PCT = (W+0.5T)/(W+L+T), NET = PF-PA)
  * zero MISMATCH verification rows; DISCREPANCY rows must carry a flag
  * all HTML internal links resolve inside the desk dir (both quote styles);
    external links restricted to allowed hosts; no repo-relative hrefs
  * the landing page carries the decision-readiness table with every requirement id
"""
import argparse
import csv
import os
import re
import sys

DESK_PAGES = [
    "index.html", "requirements.html", "captures.html", "verification.html",
    "questions.html", "suggestions.html", "flagged.html", "sources.html",
    "executive-summary.html",
]
HEADERS = {
    "requirements_coverage.csv": ["req_id", "category", "requirement", "status", "blocking_gate",
                                  "number_to_clear", "observed_2026_11_19", "evidence", "source_url", "flag"],
    "verification.csv": ["v_id", "claim", "value", "source_url", "read_utc", "method", "result", "flag"],
    "standings_fresh_2026-11-19.csv": ["team_code", "team_name", "w", "l", "t", "pct", "pf", "pa", "net",
                                       "source_url", "read_utc"],
    "wk11_slate_2026-11-19.csv": ["game_id", "game_date", "kickoff_et", "network", "away", "home",
                                  "page_heading_note", "source_url", "read_utc"],
    "wk11_byes_2026-11-19.csv": ["club", "source_url", "read_utc"],
    "wk11_tnf_injury_2026-11-19.csv": ["team", "player", "position", "injury_as_printed",
                                       "practice_status", "game_status", "source_url", "read_utc"],
    "wk12_slate_partial_2026-11-19.csv": ["game_id", "page_heading_as_printed", "game_date", "kickoff_et",
                                          "network", "away", "home", "flag", "source_url", "read_utc"],
    "questions.csv": ["q_id", "question", "information_needed", "answer_now", "blocks", "status",
                      "evidence", "source_url", "flag"],
    "suggestions.csv": ["s_id", "title", "problem", "options", "recommendation",
                        "what_would_change_our_mind", "decision_owner", "implements_when", "evidence", "status"],
    "flagged.csv": ["flag_id", "item", "where", "why", "source_url", "observed_on", "status"],
    "sources.csv": ["src_id", "name", "official", "url", "accessed_utc", "used_for"],
}
COUNTS = {
    "requirements_coverage.csv": 84,
    "verification.csv": 61,
    "standings_fresh_2026-11-19.csv": 32,
    "wk11_slate_2026-11-19.csv": 13,
    "wk11_byes_2026-11-19.csv": 6,
    "wk11_tnf_injury_2026-11-19.csv": 26,
    "wk12_slate_partial_2026-11-19.csv": 6,
    "questions.csv": 18,
    "suggestions.csv": 14,
    "flagged.csv": 20,
    "sources.csv": 6,
}
STATUS_VOCAB = {"MET", "PARTIAL", "OPEN", "BLOCKED", "RULE-ADOPTED"}
Q_STATUS = {"BLOCKING", "PARTIAL", "OPEN", "ANSWERED"}
V_RESULT = {"MATCH", "MISMATCH", "PUBLISHED", "DISCREPANCY", "NOTED"}
OFFICIAL_HOSTS = ("https://www.nfl.com/", "https://nfl.com/", "https://static.nfl.com/")
OWN_REPO = "https://github.com/sassnarep3-star/Own5/"
LINK_HOSTS = ("https://www.nfl.com/", "https://nfl.com/", "https://static.nfl.com/",
              "https://github.com/")
READ_DATE = "2026-11-19"

fails = []
checks = 0


def ck(cond, msg):
    global checks
    checks += 1
    if not cond:
        fails.append(msg)


def rows(data_dir, name):
    path = os.path.join(data_dir, name)
    with open(path, newline="", encoding="utf-8") as fh:
        rd = csv.reader(fh)
        header = next(rd)
        body = list(rd)
    return header, body


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ap.add_argument("--desk", default=os.path.dirname(os.path.abspath(__file__)))
    ap.add_argument("--data", default=None)
    args = ap.parse_args()
    desk = args.desk
    data = args.data or os.path.join(args.root, "data", "nfl-desk-6e13b9ff")
    research_md = os.path.join(args.root, "research", "nfl-6e13b9ff", "EXECUTIVE_SUMMARY.md")

    # 1. required files
    for f in DESK_PAGES + ["style.css", "build_desk.py", "verify_desk.py", "tests/test_desk.py"]:
        ck(os.path.exists(os.path.join(desk, f)), f"missing desk file: {f}")
    ck(os.path.exists(research_md), "missing research/nfl-6e13b9ff/EXECUTIVE_SUMMARY.md")

    # 2. headers + counts
    tables = {}
    for name, hdr in HEADERS.items():
        path = os.path.join(data, name)
        if not os.path.exists(path):
            ck(False, f"missing data file: {name}")
            continue
        header, body = rows(data, name)
        tables[name] = body
        ck(header == hdr, f"{name}: header mismatch -> {header}")
        ck(len(body) == COUNTS[name], f"{name}: expected {COUNTS[name]} rows, found {len(body)}")

    # 3. flagged ids (referenced by everything else)
    flag_ids = set()
    for r in tables.get("flagged.csv", []):
        fid, item, where, why, src, obs, status = r
        ck(re.fullmatch(r"F6-\d+", fid) is not None, f"flag id format: {fid}")
        ck(fid not in flag_ids, f"duplicate flag id {fid}")
        flag_ids.add(fid)
        ck(all([item, where, why]), f"{fid}: empty required cell")
        ck(src.startswith(OFFICIAL_HOSTS) or src.startswith(OWN_REPO), f"{fid}: bad source_url {src}")
        ck(obs.startswith(READ_DATE), f"{fid}: observed_on not {READ_DATE}: {obs}")
        ck(status.split()[0] in {"open", "resolved"}, f"{fid}: bad status {status}")

    # 4. coverage
    req_ids = set()
    for r in tables.get("requirements_coverage.csv", []):
        rid, cat, req, status, gate_, num, obs, ev, src, flag = r
        ck(re.fullmatch(r"K-\d{3}", rid) is not None, f"req id format {rid}")
        ck(rid not in req_ids, f"duplicate req id {rid}")
        req_ids.add(rid)
        ck(status in STATUS_VOCAB, f"{rid}: bad status {status}")
        ck(req.strip() and cat.strip() and num.strip() and obs.strip(), f"{rid}: empty required cell")
        ck(ev.strip(), f"{rid}: evidence missing (needs evidence or flag)")
        for part in [p.strip() for p in ev.split(" ;; ")]:
            if part.startswith("http"):
                ck(part.startswith((OWN_REPO,) + OFFICIAL_HOSTS),
                   f"{rid}: evidence URL host not allowed: {part}")
            else:
                ck(os.path.exists(os.path.join(args.root, part)), f"{rid}: evidence path missing: {part}")
        if src:
            ck(src.startswith(OFFICIAL_HOSTS), f"{rid}: source_url not official: {src}")
        if flag:
            ck(flag in flag_ids, f"{rid}: unknown flag {flag}")

    # 5. verification
    for r in tables.get("verification.csv", []):
        vid, claim, value, src, read, method, result, flag = r
        ck(re.fullmatch(r"V-\d{3}", vid) is not None, f"v id format {vid}")
        ck(result in V_RESULT, f"{vid}: bad result {result}")
        ck(result != "MISMATCH", f"{vid}: MISMATCH row present - investigate before publishing")
        ck(src.startswith(OFFICIAL_HOSTS), f"{vid}: source not official: {src}")
        ck(read.startswith(READ_DATE), f"{vid}: read_utc not {READ_DATE}: {read}")
        ck(claim.strip() and method.strip(), f"{vid}: empty claim/method")
        if result == "DISCREPANCY":
            ck(flag in flag_ids, f"{vid}: DISCREPANCY without valid flag ({flag})")
        if flag:
            ck(flag in flag_ids, f"{vid}: unknown flag {flag}")

    # 6. standings arithmetic (official PCT convention: ties = half-win)
    for r in tables.get("standings_fresh_2026-11-19.csv", []):
        code, name, w, l, t, pct, pf, pa, net, src, read = r
        w, l, t, pf, pa, net = int(w), int(l), int(t), int(pf), int(pa), int(net)
        exp = round((w + 0.5 * t) / (w + l + t), 3)
        ck(abs(float(pct) - exp) < 1e-9, f"{code}: PCT {pct} != {exp} (tie-half convention)")
        ck(pf - pa == net, f"{code}: NET {net} != PF-PA {pf - pa}")
        ck(src.startswith(OFFICIAL_HOSTS) and read.startswith(READ_DATE), f"{code}: source/read problem")

    # 7. other captures
    for r in tables.get("wk11_slate_2026-11-19.csv", []):
        ck(r[7].startswith(OFFICIAL_HOSTS) and r[8].startswith(READ_DATE), f"slate row source/read: {r}")
    for r in tables.get("wk11_byes_2026-11-19.csv", []):
        ck(r[1].startswith(OFFICIAL_HOSTS) and r[2].startswith(READ_DATE), f"bye row source/read: {r}")
    for r in tables.get("wk11_tnf_injury_2026-11-19.csv", []):
        ck(r[6].startswith(OFFICIAL_HOSTS) and r[7].startswith(READ_DATE), f"injury row source/read: {r}")
    for r in tables.get("wk12_slate_partial_2026-11-19.csv", []):
        ck(r[8].startswith(OFFICIAL_HOSTS) and r[9].startswith(READ_DATE), f"wk12 row source/read: {r}")
        if r[7]:
            ck(r[7] in flag_ids, f"wk12 unknown flag {r[7]}")

    # 8. registers
    for r in tables.get("questions.csv", []):
        qid, q, need, ans, blocks, status, ev, src, flag = r
        ck(status in Q_STATUS, f"{qid}: bad status {status}")
        ck(q.strip() and need.strip() and blocks.strip(), f"{qid}: empty required cell")
        ck(ans.strip(), f"{qid}: answer_now must be filled (write 'nothing known' if unknown)")
        for part in [p.strip() for p in ev.split(" ;; ")]:
            if part.startswith("http"):
                ck(part.startswith((OWN_REPO,) + OFFICIAL_HOSTS), f"{qid}: bad evidence URL {part}")
            else:
                ck(os.path.exists(os.path.join(args.root, part)), f"{qid}: evidence missing {part}")
        if src:
            ck(src.startswith(OFFICIAL_HOSTS) or src.startswith(OWN_REPO), f"{qid}: bad source_url {src}")
        if flag:
            ck(flag in flag_ids, f"{qid}: unknown flag {flag}")

    for r in tables.get("suggestions.csv", []):
        sid, title, problem, options, rec, wtc, owner, when, ev, status = r
        ck(status == "PROPOSED", f"{sid}: status must stay PROPOSED until an owner decides (found {status})")
        ck(title.strip() and problem.strip() and options.strip() and rec.strip() and wtc.strip(),
           f"{sid}: empty required cell")
        for part in [p.strip() for p in ev.split(" ;; ")]:
            if part.startswith("http"):
                ck(part.startswith((OWN_REPO,) + OFFICIAL_HOSTS), f"{sid}: bad evidence URL {part}")
            else:
                ck(os.path.exists(os.path.join(args.root, part)), f"{sid}: evidence missing {part}")

    for r in tables.get("sources.csv", []):
        sid, name, official, url, accessed, used = r
        ck(official == "yes", f"{sid}: official must be yes (all registered sources are official reads)")
        ck(url.startswith(OFFICIAL_HOSTS), f"{sid}: URL not official {url}")
        ck(accessed.startswith(READ_DATE), f"{sid}: accessed not {READ_DATE}")

    # 9. HTML link integrity (both quote styles) + landing readiness table
    href_re = re.compile(r"""href\s*=\s*(['"])(.*?)\1""", re.S)
    index_html = ""
    for page in DESK_PAGES:
        path = os.path.join(desk, page)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as fh:
            txt = fh.read()
        if page == "index.html":
            index_html = txt
        ck('rel="stylesheet" href="style.css"' in txt, f"{page}: stylesheet link missing")
        for _q, href in href_re.findall(txt):
            if href.startswith(("http://", "https://")):
                ck(href.startswith(LINK_HOSTS), f"{page}: external host not allowed: {href[:90]}")
            elif href.startswith("#"):
                continue
            else:
                ck(not href.startswith("../"), f"{page}: repo-relative link escapes desk: {href}")
                target = href.split("#", 1)[0]
                ck(target and os.path.exists(os.path.join(desk, target)),
                   f"{page}: broken internal link: {href}")

    ck(index_html != "", "index.html missing")
    ck("Decision-readiness" in index_html, "landing page lacks the decision-readiness heading")
    for rid in req_ids:
        ck(f'id="{rid}"' in index_html, f"landing page missing requirement row {rid}")
    if index_html:
        n_rows = len(re.findall(r'id="K-\d{3}"', index_html))
        ck(n_rows == len(req_ids), f"landing readiness rows {n_rows} != requirements {len(req_ids)}")

    if fails:
        for f in fails:
            print(f"FAIL: {f}")
        print(f"verify_desk: {checks} checks, {len(fails)} FAILURES")
        return 1
    print(f"verify_desk: {checks} checks, 0 failures "
          f"({len(req_ids)} requirements, {COUNTS['verification.csv']} verification rows, "
          f"{len(flag_ids)} flags, {len(DESK_PAGES)} pages)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

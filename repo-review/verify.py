"""Fail-closed checks for the repository review.

Checks: registers have the expected headers and no blank required fields; every row carries an https
source link (GitHub file or nfl.com); result vocabularies are closed; irregularity IDs are unique and
every FIXED item says what was done; page row counts equal register counts; every internal link on the
review pages and the integration-hub link resolves. Run: python3 repo-review/verify.py
"""
from __future__ import annotations

import csv
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
DATA = HERE / "data"
ALLOWED_HOSTS = {"github.com", "www.nfl.com", "nfl.com", "static.www.nfl.com", "sassnarep3-star.github.io"}
EXPECTED = {
    "inventory.csv": ["directory", "scope", "tracked_files", "entry_point", "live_url", "verifier", "verifier_result", "workflow_files", "source_url"],
    "verifier_runs.csv": ["directory", "command", "exit_code", "result", "summary_line", "run_utc", "source_url", "workflow_files"],
    "standings_check.csv": ["team", "official_wlt", "official_pf_pa", "desk_e1d60f5d_wlt", "desk_e1d60f5d_pf_pa", "result_desk_e1d60f5d",
                            "hub_official_wlt_dated_2026_11_13", "hub_official_pf_pa", "result_hub", "official_source_url", "desk_source_url"],
    "spot_checks.csv": ["check_id", "area", "official_url", "official_observation", "desk_value", "desk_url", "result", "read_date", "notes"],
    "irregularities.csv": ["flag_id", "severity", "area", "observation", "evidence_url", "evidence_detail", "official_url", "status", "action_needed"],
}
RESULTS = {
    "spot_checks.csv": {"MATCH", "MISMATCH", "NOT CHECKED", "UNVERIFIED"},
    "verifier_runs.csv": {"PASS", "FAIL"},
    "irregularities.csv": {"HIGH", "MEDIUM", "LOW"},
}
errors: list[str] = []
checks = 0


def check(cond: bool, msg: str) -> None:
    global checks
    checks += 1
    if not cond:
        errors.append(msg)


def load(name: str) -> list[dict[str, str]]:
    path = DATA / name
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        check(reader.fieldnames == EXPECTED[name], f"{name}: header mismatch {reader.fieldnames}")
        rows = list(reader)
    check(bool(rows), f"{name}: no rows")
    for i, row in enumerate(rows, 2):
        check(None not in row, f"{name}:{i}: malformed row")
    return rows


def https_ok(url: str) -> bool:
    p = urlparse(url)
    return p.scheme == "https" and p.hostname in ALLOWED_HOSTS


class Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hrefs: list[str] = []
        self.ids: set[str] = set()
        self.rows = 0
        self.in_tbody = False

    def handle_starttag(self, tag: str, attrs) -> None:
        d = dict(attrs)
        if d.get("href"):
            self.hrefs.append(d["href"] or "")
        if d.get("id"):
            self.ids.add(d["id"] or "")
        if tag == "tbody":
            self.in_tbody = True
        if tag == "tr" and self.in_tbody:
            self.rows += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "tbody":
            self.in_tbody = False


def main() -> int:
    inv = load("inventory.csv")
    runs = load("verifier_runs.csv")
    stand = load("standings_check.csv")
    spots = load("spot_checks.csv")
    flags = load("irregularities.csv")

    for r in inv:
        check(https_ok(r["source_url"]) or r["source_url"].startswith(f"https://github.com/sassnarep3-star/Own5/"), f"inventory {r['directory']}: source not allowed")
        check(r["verifier_result"] in {"PASS", "FAIL", "NO VERIFIER", "RUN IN CI"}, f"inventory {r['directory']}: bad verifier_result")
    for r in runs:
        check(https_ok(r["source_url"]), f"verifier {r['directory']}: source not allowed")
        check(r["result"] in RESULTS["verifier_runs.csv"], f"verifier {r['directory']}: bad result {r['result']}")
        check(r["exit_code"].lstrip("-").isdigit(), f"verifier {r['directory']}: non-numeric exit code")
        check((r["result"] == "PASS") == (r["exit_code"] == "0"), f"verifier {r['directory']}: result and exit code disagree")
    verifier_dirs = {p.parent.name for p in REPO.glob("*/verify.py") if p.parent.name != "repo-review"}
    check(verifier_dirs == {r["directory"] for r in runs}, "verifier_runs.csv does not list every verify.py in the repo")

    for r in stand:
        ok = r["result_desk_e1d60f5d"] in {"MATCH", "MISMATCH"} and r["result_hub"] in {"MATCH", "MISMATCH"}
        check(ok, f"standings {r['team']}: bad result value")
        check(https_ok(r["official_source_url"]) and https_ok(r["desk_source_url"]), f"standings {r['team']}: source not allowed")
    check(len(stand) == 32, f"standings_check.csv has {len(stand)} rows, expected 32")
    check(len({r["team"] for r in stand}) == 32, "standings_check.csv team names are not unique")

    for r in spots:
        check(https_ok(r["official_url"]) or r["official_url"].startswith(f"{'https://github.com/sassnarep3-star/Own5/'}"), f"spot {r['check_id']}: official_url not allowed")
        check(https_ok(r["desk_url"]), f"spot {r['check_id']}: desk_url not allowed")
        check(r["result"].split(" (")[0] in RESULTS["spot_checks.csv"], f"spot {r['check_id']}: result vocabulary {r['result']}")
    check(len({r["check_id"] for r in spots}) == len(spots), "spot-check IDs are not unique")

    ids = [f["flag_id"] for f in flags]
    check(len(ids) == len(set(ids)), "irregularity IDs are not unique")
    for f in flags:
        check(f["severity"] in RESULTS["irregularities.csv"], f"{f['flag_id']}: bad severity")
        check(https_ok(f["evidence_url"]), f"{f['flag_id']}: evidence link not allowed")
        if f["official_url"]:
            check(https_ok(f["official_url"]), f"{f['flag_id']}: official link not allowed")
        check(bool(f["action_needed"].strip()), f"{f['flag_id']}: no action")
        if f["status"].startswith("FIXED"):
            check(bool(f["action_needed"].strip()), f"{f['flag_id']}: FIXED without a note")

    # Page checks: table rows = register rows + header, and internal links resolve.
    pages = {
        "inventory.html": len(inv), "verifiers.html": len(runs), "flagged.html": len(flags),
        "spot-checks.html": len(spots) + len(stand),
    }
    for name, expected in pages.items():
        path = HERE / name
        check(path.exists(), f"missing page {name}")
        if not path.exists():
            continue
        parser = Links()
        parser.feed(path.read_text(encoding="utf-8"))
        # spot-checks has two tables; others have one. Row counts are per table tbody.
        check(parser.rows == expected, f"{name}: tbody rows {parser.rows} != register rows {expected}")
        for href in parser.hrefs:
            if href.startswith(("http://", "https://", "mailto:")):
                check(https_ok(href) or href.startswith("https://github.com/"), f"{name}: external link not allowed: {href}")
                continue
            if href.startswith("#"):
                check(href[1:] in parser.ids or href == "#main" or href == "#", f"{name}: missing anchor {href}")
                continue
            target = (path.parent / unquote(href.split("#")[0])).resolve()
            check(target.exists(), f"{name}: broken internal link {href}")
    index = (HERE / "index.html")
    check(index.exists(), "index.html missing")

    print(f"repo-review verify: {checks} checks, {len(errors)} failure(s)")
    for e in errors:
        print("FAIL", e)
    if errors:
        return 1
    print("PASS: repo-review registers, source links, row counts and internal links are consistent")
    return 0


if __name__ == "__main__":
    sys.exit(main())

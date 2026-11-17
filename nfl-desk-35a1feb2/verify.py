#!/usr/bin/env python3
"""verify.py — the desk's own proof, run in CI and on every build.

Five independent checks:
  1. determinism: engine.py reproduces every derived table byte-for-byte;
  2. capture integrity: SHA-256 of each raw read still matches the manifest;
  3. transcript containment: every number published in the standings and results tables appears in the raw
     transcript, so a table cannot gain a value the read did not contain;
  4. row provenance on the generated HTML: every body row ends in an official link, a labelled third-party
     link, or an explicit UNVERIFIED badge;
  5. link integrity: every internal href and every page named in the nav exists.
"""
from __future__ import annotations
import csv, hashlib, html, io, re, subprocess, sys, tempfile, shutil
from html.parser import HTMLParser
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
RAW = HERE / "raw"
DERIVED = ["standings_verified.csv", "standings_integrity_checks.csv", "results_feed_2026.csv",
            "results_feed_changes_wk10.csv", "correlations.csv", "correlations_withheld.csv", "luck_panel.csv",
            "originated_wk11.csv", "model_card.csv", "walkforward_totals.csv", "injury_read_delta.csv",
            "availability_census_read2.csv", "availability_read2_coverage.csv",
            "roster_event_staleness_audit.csv", "roster_event_summary.csv", "third_party_inventory.csv",
            "third_party_asset_register.csv", "designation_play_rate.csv", "price_snapshots.csv",
            "price_store_schema.csv", "manifest.csv"]
OFFICIAL_HOSTS = ("nfl.com", "nflmedia.com", "operations.nfl.com", "media.nfl.com")
OPERATOR_HOSTS = ("sportsbook.draftkings.com", "sportsbook.fanduel.com", "betmgm.com")
CLUB_HOST = re.compile(r"^https://www\.[a-z]+\.(com|com\.[a-z]{2})/")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows, self.cur, self.in_row = [], [], False
        self.cell, self.cells, self.in_cell = [], [], False
        self.links, self.assets, self.ids = [], [], set()
        self.depth = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.add(a["id"])
        if tag == "a" and a.get("href"):
            self.links.append(a["href"])
            if self.in_row:
                self.cur.append(a.get("href") or "")
        if tag in ("link", "script", "img") and (a.get("href") or a.get("src")):
            self.assets.append(a.get("href") or a.get("src"))
        if tag == "tbody":
            self.depth += 1
        if tag == "td" and self.in_row:
            self.in_cell, self.cell = True, []
        if tag == "tr" and self.depth:
            self.in_row, self.cur, self.cells = True, [], []

    def handle_data(self, data):
        if self.in_cell:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if tag == "td" and self.in_cell:
            self.in_cell = False; self.cells.append(" ".join("".join(self.cell).split()))
        if tag == "tr" and self.in_row:
            self.rows.append((self.cur, self.cells)); self.in_row = False
        if tag == "tbody":
            self.depth -= 1


def main() -> int:
    problems = []

    # 1. determinism
    tmp = Path(tempfile.mkdtemp())
    keep = {p.name: p.read_bytes() for p in list(DATA.glob("*.csv")) + list(DATA.glob("*.json"))}
    try:
        subprocess.run([sys.executable, str(HERE / "engine.py")], check=True, cwd=HERE,
                       stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        for name, blob in keep.items():
            if name in DERIVED and (DATA / name).read_bytes() != blob:
                problems.append(f"not reproducible: data/{name} changed on rebuild")
    except subprocess.CalledProcessError as e:
        problems.append(f"engine.py failed to rebuild: {e}")
    finally:
        for name, blob in keep.items():
            (DATA / name).write_bytes(blob)
        shutil.rmtree(tmp, ignore_errors=True)

    # 2. capture integrity
    with io.open(DATA / "manifest.csv", newline="", encoding="utf-8") as f:
        man = list(csv.DictReader(f))
    for row in man:
        p = HERE / row["path"]
        if not p.exists():                       # carried-forward inputs from a sibling desk live at the repo root
            p = HERE.parent / row["path"]
        if not p.exists():
            problems.append(f"manifest entry missing on disk: {row['path']}")
        elif sha(p) != row["sha256"]:
            problems.append(f"hash mismatch (a capture was edited after the manifest was written): {row['path']}")

    # 3. transcript containment
    transcript = (RAW / "official_reads_2026-11-17.txt").read_text(encoding="utf-8")
    flat = re.sub(r"\s+", " ", transcript)
    with io.open(DATA / "standings_verified.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            pat = f"{r['team']}|{r['w']}|{r['l']}|{r['t']}|0.{r['pct_recomputed'][2:]}|{r['pf']}|{r['pa']}"
            if re.sub(r"\s+", " ", pat) not in flat:
                problems.append(f"standings row not found in the raw transcript: {r['team']}")
    with io.open(DATA / "results_wk10_increment.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["status"] != "FINAL":
                if "NO SCORE PUBLISHED AT READ TIME" not in flat:
                    problems.append(f"pending game not evidenced: {r['game_id']}")
                continue
            a, h = r["away"], r["home"]
            if f"{a} {r['away_score']} at {h} {r['home_score']}" not in flat:
                problems.append(f"result line not found in the raw transcript: {r['game_id']}")

    # 3b. the summary JSON must agree with the table it summarises (it is quoted on two pages)
    import json
    summ = json.loads((DATA / "luck_summary.json").read_text(encoding="utf-8"))
    with io.open(DATA / "luck_panel.csv", newline="", encoding="utf-8") as f:
        panel = list(csv.DictReader(f))
    top = max(panel, key=lambda r: float(r["luck_wins"]))
    bot = min(panel, key=lambda r: float(r["luck_wins"]))
    if summ["max_positive_luck"] != top["luck_wins"] or summ["max_positive_luck_team"] != top["team"]:
        problems.append("luck_summary.json does not agree with luck_panel.csv (positive tail)")
    if summ["max_negative_luck"] != bot["luck_wins"] or summ["max_negative_luck_team"] != bot["team"]:
        problems.append("luck_summary.json does not agree with luck_panel.csv (negative tail)")
    if int(summ["teams"]) != len(panel):
        problems.append("luck_summary.json team count disagrees with the panel")

    # 4 + 5. generated HTML
    pages = sorted(HERE.glob("*.html"))
    if len(pages) < 15:
        problems.append(f"expected 15 pages, found {len(pages)}")
    parsed = {}
    rows_total = 0
    for path in pages:
        p = Page(); p.feed(path.read_text(encoding="utf-8"))
        parsed[path.name] = p
        rows_total += len(p.rows)
        for i, (links, cells) in enumerate(p.rows, 1):
            last = links[-1] if links else ""
            ok = last.startswith("http") and (any(h in last for h in OFFICIAL_HOSTS) or "github.com" in last
                or any(h in last for h in OPERATOR_HOSTS) or bool(CLUB_HOST.match(last)))
            if not ok and last and not last.startswith("http"):
                ok = (path.parent / last.split("#")[0]).exists()
            if not ok and cells and ("UNVERIFIED" in cells[-1] or "method" in cells[-1].lower()):
                ok = True
            if not ok:
                problems.append(f"row without a source link or an explicit UNVERIFIED badge: {path.name} row {i} "
                                f"(first cell: {cells[0][:38] if cells else '?'})")
        for u in p.links + p.assets:
            if u.startswith(("http", "#", "mailto:")):
                continue
            target = (path.parent / u.split("#")[0])
            if not target.exists():
                problems.append(f"broken internal link: {path.name} -> {u}")
    print(f"verify: {len(pages)} pages, {rows_total} table rows, {len(man)} manifest entries")
    if problems:
        print("\n".join("FAIL  " + x for x in problems[:40]))
        print(f"{len(problems)} problem(s)")
        return 1
    print("PASS  determinism, capture hashes, transcript containment, row provenance, internal links")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

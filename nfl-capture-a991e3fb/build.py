#!/usr/bin/env python3
"""Build the live Week 10 injury-report capture, its checks, and its page.

Inputs
  raw/reg10_official_transcription.txt   transcription of the official nfl.com page (see header)
  ../data/decision-desk/official/official_injuries_wk10.csv   the previously published table
  ../data/bye-weeks-2026.csv             bye weeks (cross-check for missing clubs)

Outputs (all deterministic, stdlib only)
  data/official_injury_report_wk10_live.csv
  data/diff_vs_published_wk10.csv
  data/checks.csv
  index.html
Exit status is non-zero if any hard check fails.
"""
import csv
import html
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
OFFICIAL_URL = "https://www.nfl.com/injuries/league/2026/reg10"
FETCHED_BEFORE = "2026-11-15T23:24:44Z"

# abbr -> (nickname as printed on the page, full name used in the bye-week file)
TEAMS = {
    "ARI": ("Cardinals", "Arizona Cardinals"), "ATL": ("Falcons", "Atlanta Falcons"),
    "BAL": ("Ravens", "Baltimore Ravens"), "BUF": ("Bills", "Buffalo Bills"),
    "CAR": ("Panthers", "Carolina Panthers"), "CHI": ("Bears", "Chicago Bears"),
    "CIN": ("Bengals", "Cincinnati Bengals"), "CLE": ("Browns", "Cleveland Browns"),
    "DAL": ("Cowboys", "Dallas Cowboys"), "DEN": ("Broncos", "Denver Broncos"),
    "DET": ("Lions", "Detroit Lions"), "GB": ("Packers", "Green Bay Packers"),
    "HOU": ("Texans", "Houston Texans"), "IND": ("Colts", "Indianapolis Colts"),
    "JAX": ("Jaguars", "Jacksonville Jaguars"), "KC": ("Chiefs", "Kansas City Chiefs"),
    "LAC": ("Chargers", "Los Angeles Chargers"), "LAR": ("Rams", "Los Angeles Rams"),
    "LV": ("Raiders", "Las Vegas Raiders"), "MIA": ("Dolphins", "Miami Dolphins"),
    "MIN": ("Vikings", "Minnesota Vikings"), "NE": ("Patriots", "New England Patriots"),
    "NO": ("Saints", "New Orleans Saints"), "NYG": ("Giants", "New York Giants"),
    "NYJ": ("Jets", "New York Jets"), "PHI": ("Eagles", "Philadelphia Eagles"),
    "PIT": ("Steelers", "Pittsburgh Steelers"), "SEA": ("Seahawks", "Seattle Seahawks"),
    "SF": ("49ers", "San Francisco 49ers"), "TB": ("Buccaneers", "Tampa Bay Buccaneers"),
    "TEN": ("Titans", "Tennessee Titans"), "WAS": ("Commanders", "Washington Commanders"),
}
NICK_TO_ABBR = {v[0]: k for k, v in TEAMS.items()}

# Reader tallies taken while reading the page; the build fails if the transcription disagrees.
EXPECTED_ROWS = {
    "WAS": 9, "NYG": 11, "NE": 15, "DET": 9, "KC": 13, "ATL": 11, "MIN": 13, "GB": 17,
    "JAX": 11, "TEN": 12, "BUF": 14, "NYJ": 9, "MIA": 11, "IND": 14, "CAR": 12, "NO": 12,
    "HOU": 16, "CLE": 12, "LAR": 14, "ARI": 15, "SEA": 15, "LV": 5, "SF": 12, "DAL": 19,
    "PIT": 8, "CIN": 9, "LAC": 19, "BAL": 10,
}
PRACTICE_OK = {
    "Full Participation in Practice", "Limited Participation in Practice",
    "Did Not Participate In Practice", "",
}
GAME_OK = {"", "Out", "Questionable", "Doubtful"}


def parse_transcription():
    rows, sections, cur = [], [], None
    for raw_line in (HERE / "raw" / "reg10_official_transcription.txt").read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        if not line:
            continue
        if line.startswith("## "):
            head = [p.strip() for p in line[3:].split("|")]
            cur = {"abbr": head[0], "nick": head[1], "slot": head[2], "network": head[3]}
            sections.append(cur)
            continue
        if line.startswith("#"):
            continue
        parts = line.split("|")
        if len(parts) != 5:
            raise SystemExit(f"bad row (expected 5 fields): {line!r}")
        player, pos, injury, practice, game = [p.strip() for p in parts]
        rows.append({
            "week": "10", "team_abbr": cur["abbr"], "team_nickname": cur["nick"],
            "game_slot": cur["slot"], "network": cur["network"],
            "player": player, "position": pos, "injury": injury,
            "practice_status": practice, "game_status": game,
            "source_url": OFFICIAL_URL, "fetched_before_utc": FETCHED_BEFORE,
        })
    return rows, sections


def load_published():
    path = REPO / "data" / "decision-desk" / "official" / "official_injuries_wk10.csv"
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def main():
    rows, sections = parse_transcription()
    checks = []

    def check(name, ok, detail):
        checks.append({"check": name, "result": "PASS" if ok else "FAIL", "detail": detail})

    # 1. per-section counts against the reader tallies
    counts = {}
    for r in rows:
        counts[r["team_abbr"]] = counts.get(r["team_abbr"], 0) + 1
    mismatch = {k: (counts.get(k, 0), v) for k, v in EXPECTED_ROWS.items() if counts.get(k, 0) != v}
    check("section row counts match reader tallies", not mismatch, f"mismatches={mismatch}" if mismatch else f"{len(EXPECTED_ROWS)} sections")

    # 2. nicknames match the team map
    bad_nick = [s for s in sections if TEAMS.get(s["abbr"], ("",))[0] != s["nick"]]
    check("section codes agree with nicknames", not bad_nick, f"bad={bad_nick}" if bad_nick else "all agree")

    # 3. vocabulary
    bad_vocab = [r for r in rows if r["practice_status"] not in PRACTICE_OK or r["game_status"] not in GAME_OK]
    check("practice/game status vocabulary", not bad_vocab, f"bad={len(bad_vocab)}" if bad_vocab else "all values in the published vocabulary")

    # 4. every row has required fields + a source link
    missing = [r for r in rows if not r["player"] or not r["position"] or not r["source_url"].startswith("https://www.nfl.com/")]
    check("required fields and official source link on every row", not missing, f"missing={len(missing)}")

    # 5. clubs with no section must be exactly the Week 10 byes
    bye_rows = list(csv.DictReader((REPO / "data" / "bye-weeks-2026.csv").open(encoding="utf-8-sig", newline="")))
    wk10 = next(r for r in bye_rows if r["week"] == "10")
    bye_names = {n.strip() for n in wk10["teams_on_bye"].split(";")}
    absent = {a for a, (_, full) in TEAMS.items() if a not in counts}
    absent_names = {TEAMS[a][1] for a in absent}
    check("clubs without a section = Week 10 bye clubs", absent_names == bye_names,
          f"absent={sorted(absent)} bye_file={sorted(bye_names)}")
    check("32 clubs covered (28 with a section + 4 byes)", len(counts) == 28 and len(absent) == 4,
          f"sections={len(counts)} absent={len(absent)}")

    # 6. the three Lions rows the earlier table left blank
    lions = {r["player"]: r for r in rows if r["team_abbr"] == "DET"}
    lions_ok = all(lions[p]["game_status"] == "Out" for p in ("Kerby Joseph", "Cade Mays", "D.J. Reed"))
    check("Lions: Joseph, Mays, Reed listed Out", lions_ok, "; ".join(f"{p}={lions[p]['game_status'] or 'blank'}" for p in ("Kerby Joseph", "Cade Mays", "D.J. Reed")))

    # 7. no duplicate player within a club
    seen, dups = set(), []
    for r in rows:
        key = (r["team_abbr"], r["player"])
        if key in seen:
            dups.append(key)
        seen.add(key)
    check("no duplicate player within a club", not dups, f"dups={dups}" if dups else "none")

    # 8. diff against the previously published Week 10 table
    published = load_published()
    pub = {}
    for r in published:
        abbr = NICK_TO_ABBR.get(r["team_nickname"])
        pub[(abbr, r["player"])] = r
    live = {(r["team_abbr"], r["player"]): r for r in rows}
    diff = []
    for key, r in live.items():
        if key not in pub:
            diff.append(dict(team=r["team_nickname"], player=r["player"], change="added in live report",
                             pub_practice="", live_practice=r["practice_status"], pub_game="", live_game=r["game_status"]))
            continue
        p = pub[key]
        if (p["practice_status"], p["game_status"]) != (r["practice_status"], r["game_status"]):
            change = "game status blank -> " + (r["game_status"] or "blank") if not p["game_status"] and r["game_status"] else "status changed"
            diff.append(dict(team=r["team_nickname"], player=r["player"], change=change,
                             pub_practice=p["practice_status"], live_practice=r["practice_status"],
                             pub_game=p["game_status"], live_game=r["game_status"]))
    for key, p in pub.items():
        if key not in live:
            diff.append(dict(team=p["team_nickname"], player=p["player"], change="in published table, not in live report",
                             pub_practice=p["practice_status"], live_practice="", pub_game=p["game_status"], live_game=""))
    pub_teams = {NICK_TO_ABBR.get(r["team_nickname"]) for r in published}
    pub_rows = len(published)
    live_rows = len(rows)
    teams_missing_pub = sorted({TEAMS[a][0] for a in counts} - {TEAMS[a][0] for a in pub_teams if a})
    checks.append({"check": "published table: row count", "result": "INFO",
                   "detail": f"published={pub_rows} live={live_rows}"})
    checks.append({"check": "published table: clubs with no rows", "result": "INFO",
                   "detail": "; ".join(teams_missing_pub) or "none"})
    checks.append({"check": "published table: rows changed or added or removed", "result": "INFO",
                   "detail": f"{len(diff)} rows (see diff_vs_published_wk10.csv)"})

    # outputs
    data = HERE / "data"
    data.mkdir(exist_ok=True)
    cols = ["week", "team_abbr", "team_nickname", "game_slot", "network", "player", "position", "injury",
            "practice_status", "game_status", "source_url", "fetched_before_utc"]
    with (data / "official_injury_report_wk10_live.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    with (data / "diff_vs_published_wk10.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["team", "player", "change", "pub_practice", "live_practice", "pub_game", "live_game"])
        w.writeheader()
        w.writerows(sorted(diff, key=lambda d: (d["team"], d["player"])))
    with (data / "checks.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["check", "result", "detail"])
        w.writeheader()
        w.writerows(checks)

    (HERE / "index.html").write_text(render(rows, sections, checks, diff, published), encoding="utf-8")

    failed = [c for c in checks if c["result"] == "FAIL"]
    print(f"live rows={live_rows} sections={len(counts)} published rows={pub_rows} diff rows={len(diff)}")
    for c in checks:
        print(f"  [{c['result']}] {c['check']}: {c['detail']}")
    return 1 if failed else 0


def esc(s):
    return html.escape(str(s if s is not None else ""))


def render(rows, sections, checks, diff, published):
    fails = sum(1 for c in checks if c["result"] == "FAIL")
    css = """
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0;background:#f6f7f9;color:#1d2330;line-height:1.45}
header{background:#13233f;color:#fff;padding:22px 28px}
header a{color:#9fd0ff}
main{max-width:1200px;margin:0 auto;padding:22px 28px}
h1{margin:0 0 6px;font-size:1.6rem} h2{font-size:1.2rem;margin:28px 0 10px}
.cards{display:flex;gap:12px;flex-wrap:wrap}
.card{background:#fff;border:1px solid #dde2ea;border-radius:8px;padding:12px 16px;min-width:150px}
.card b{display:block;font-size:1.4rem}
table{border-collapse:collapse;width:100%;background:#fff;font-size:.9rem;margin-bottom:8px}
th,td{border-bottom:1px solid #e5e9f0;padding:6px 8px;text-align:left;vertical-align:top}
th{background:#eef2f7;position:sticky;top:0}
.pass{color:#11672f;font-weight:600}.fail{color:#b00020;font-weight:700}.info{color:#4b5563}
.flag{background:#fff4d6;border:1px solid #f1d27a;border-radius:8px;padding:12px 16px}
.badge{display:inline-block;background:#fde2e2;color:#8a1c1c;border-radius:4px;padding:1px 6px;font-size:.78rem}
.wrap{overflow-x:auto;max-height:720px}
"""
    out = []
    out.append(f"<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
               f"<title>Week 10 official injury report: live capture (a991e3fb)</title><style>{css}</style></head><body>")
    out.append("<header><h1>Week 10 official injury report: live capture</h1>"
               "<div>Rebuilt from the official NFL.com injury report for Week 10 of the 2026 season. "
               f"<a href='{OFFICIAL_URL}'>Official page &rarr;</a> &middot; "
               "<a href='../'>&larr; repo index</a></div></header><main>")
    out.append("<div class='cards'>")
    out.append(f"<div class='card'>Rows in live official report<b>{len(rows)}</b></div>")
    out.append(f"<div class='card'>Clubs with a section<b>{len({r['team_abbr'] for r in rows})}</b></div>")
    out.append(f"<div class='card'>Rows in previously published table<b>{len(published)}</b></div>")
    out.append(f"<div class='card'>Rows that differ from the published table<b>{len(diff)}</b></div>")
    out.append(f"<div class='card'>Hard checks failing<b class='{'fail' if fails else 'pass'}'>{fails}</b></div>")
    out.append("</div>")

    out.append("<h2>Flagged for review</h2><div class='flag'><ul>")
    out.append("<li><b>Previously published table was stale.</b> It was captured 2026-11-12T16:52:39Z from the generic /injuries/ URL, "
               f"holds {len(published)} rows, and has no Ravens or Chargers sections. The live Week 10 report has {len(rows)} rows across 28 clubs.</li>")
    out.append("<li><b>Lions game status.</b> The published table left Kerby Joseph, Cade Mays and D.J. Reed blank and showed Joseph as Limited. "
               "The official page lists all three as Did Not Participate and Out.</li>")
    out.append("<li><b>Week 11 report not yet published.</b> The page /injuries/league/2026/reg11 returned the Week 10 page (canonical URL reg10). "
               "No Week 11 report was available at capture time, so no Week 11 designations are shown here.</li>")
    out.append("<li><b>Transcription, not a machine download.</b> Bash in this sandbox cannot reach nfl.com. Rows were transcribed from the fetch tool's output "
               "(8 chunks). Per-club counts were checked against reader tallies and the four byes against the bye-week file. "
               "A reviewer should still spot-check any row against the official page.</li>")
    out.append("<li><b>Designations not inferred.</b> A player missing from a club's list is shown as absent, not as healthy. "
               "The official news items on the same page (for example, Malik Willis placed on injured reserve, Lamar Jackson on injured reserve) are cited, not converted into rows.</li>")
    out.append("</ul></div>")

    out.append("<h2>Hard checks</h2><table><tr><th>Check</th><th>Result</th><th>Detail</th></tr>")
    for c in checks:
        cls = {"PASS": "pass", "FAIL": "fail"}.get(c["result"], "info")
        out.append(f"<tr><td>{esc(c['check'])}</td><td class='{cls}'>{esc(c['result'])}</td><td>{esc(c['detail'])}</td></tr>")
    out.append("</table>")

    out.append(f"<h2>Changes against the previously published Week 10 table ({len(diff)} rows)</h2>")
    out.append("<div class='wrap'><table><tr><th>Club</th><th>Player</th><th>Change</th><th>Published practice</th><th>Live practice</th><th>Published game</th><th>Live game</th><th>Source</th></tr>")
    for d in sorted(diff, key=lambda d: (d["team"], d["player"])):
        out.append("<tr>" + "".join(f"<td>{esc(d[k])}</td>" for k in ("team", "player", "change", "pub_practice", "live_practice", "pub_game", "live_game"))
                   + f"<td><a href='{OFFICIAL_URL}'>nfl.com</a></td></tr>")
    out.append("</table></div>")

    out.append(f"<h2>Live Week 10 report, all {len(rows)} rows</h2>")
    out.append("<div class='wrap'><table><tr><th>Game</th><th>Club</th><th>Player</th><th>Pos</th><th>Injury</th><th>Practice status</th><th>Game status</th><th>Source</th></tr>")
    for r in rows:
        game = f"{r['game_slot']}"
        gs = esc(r["game_status"]) or "<span class='badge'>blank</span>"
        out.append(f"<tr><td>{esc(game)}</td><td>{esc(r['team_nickname'])}</td><td>{esc(r['player'])}</td><td>{esc(r['position'])}</td>"
                   f"<td>{esc(r['injury'])}</td><td>{esc(r['practice_status'])}</td>"
                   f"<td>{gs}</td>"
                   f"<td><a href='{OFFICIAL_URL}'>nfl.com</a></td></tr>")
    out.append("</table></div>")
    out.append("<p class='info'>Blank game status means the official page shows no game designation for that player. "
               "Players with a blank injury cell are on the report with no listed injury.</p>")
    out.append("</main></body></html>")
    return "".join(out)


if __name__ == "__main__":
    sys.exit(main())

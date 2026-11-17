#!/usr/bin/env python3
"""Build and verify the a699fc53 audit pages.

Inputs (all in this repository):
  nfl-audit-a699fc53/data/official_injury_report_wk10_2026.csv  official rows, transcribed from nfl.com
  nfl-audit-a699fc53/data/official_transactions_nov_2026.csv    official trades and reserve-list rows
  nfl-audit-a699fc53/data/brief_claims_check.csv                claim-by-claim verdicts
  nfl-audit-a699fc53/data/flagged.csv                           Flagged for Review register
  nfl-desk-e46fb855/data/injuries.csv                           the published desk table being compared (read-only)
  nfl-desk-e46fb855/data/bye_weeks_2026.csv                     published bye file being checked (read-only)
  data/bye-weeks-2026.csv                                       root bye file (read-only)

Outputs (generated, deterministic):
  nfl-audit-a699fc53/data/comparison_wk10.csv, summary.json
  nfl-audit-a699fc53/index.html, comparison.html, transactions.html, flagged.html

Every check below either passes or raises SystemExit with the failing check named.
Nothing is filled in: a value that is not in the inputs is rendered as blank.
"""
from __future__ import annotations

import csv
import html
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DATA = HERE / "data"
DESK = ROOT / "nfl-desk-e46fb855"

OFF_CSV = DATA / "official_injury_report_wk10_2026.csv"
TX_CSV = DATA / "official_transactions_nov_2026.csv"
CLAIMS_CSV = DATA / "brief_claims_check.csv"
FLAG_CSV = DATA / "flagged.csv"
PUB_CSV = DESK / "data" / "injuries.csv"
PUB_BYE_CSV = DESK / "data" / "bye_weeks_2026.csv"
ROOT_BYE_CSV = ROOT / "data" / "bye-weeks-2026.csv"

REPORT_URL = "https://www.nfl.com/injuries/league/2026/reg10"
REG11_URL = "https://www.nfl.com/injuries/league/2026/reg11"
TRADES_URL = "https://www.nfl.com/transactions/league/trades/2026/11"
RESERVE_NOV_URL = "https://www.nfl.com/transactions/league/reserve-list/2026/11"
RESERVE_OCT_URL = "https://www.nfl.com/transactions/league/reserve-list/2026/10"
MAIN_DESK = "../nfl-desk-e46fb855/index.html"

# Hand-counted from the official page before transcription; the build proves the
# transcription matches these counts club by club.
EXPECTED_OFFICIAL_PER_CLUB = {
    "WAS": 9, "NYG": 11, "NE": 15, "DET": 9, "KC": 13, "ATL": 11, "MIN": 13,
    "GB": 17, "JAX": 11, "TEN": 12, "BUF": 14, "NYJ": 9, "MIA": 11, "IND": 14,
    "CAR": 12, "NO": 12, "HOU": 16, "CLE": 12, "LAR": 14, "AZ": 15, "SEA": 15,
    "LV": 5, "SF": 12, "DAL": 19, "PIT": 8, "CIN": 9, "LAC": 19, "BAL": 10,
}
EXPECTED_OFFICIAL_TOTAL = 347
ALL_32 = sorted([
    "ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE", "DAL", "DEN", "DET",
    "GB", "HOU", "IND", "JAX", "KC", "LAC", "LAR", "LV", "MIA", "MIN", "NE", "NO",
    "NYG", "NYJ", "PHI", "PIT", "SEA", "SF", "TB", "TEN", "WAS",
])
# Official page code -> desk code. The official page uses AZ for Arizona.
CODE_MAP = {"AZ": "ARI"}
EXPECTED_BYES_WK10 = ["CHI", "DEN", "PHI", "TB"]

FAILURES: list[str] = []


def check(cond: bool, label: str) -> None:
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {label}")
    if not cond:
        FAILURES.append(label)


def norm_name(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z]", "", s)


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def esc(s: str) -> str:
    return html.escape(s or "", quote=True)


def fmt_blank(s: str) -> str:
    """Blank is shown as an explicit dash-free empty cell with a badge, never a guess."""
    s = (s or "").strip()
    return esc(s) if s else '<span class="blank">blank</span>'


# ----------------------------------------------------------------------------
# Load and compare
# ----------------------------------------------------------------------------

def load() -> dict:
    off = read_csv(OFF_CSV)
    pub = read_csv(PUB_CSV)
    tx = read_csv(TX_CSV)
    claims = read_csv(CLAIMS_CSV)
    flags = read_csv(FLAG_CSV)
    pub_bye = read_csv(PUB_BYE_CSV)
    root_bye = read_csv(ROOT_BYE_CSV)
    return dict(off=off, pub=pub, tx=tx, claims=claims, flags=flags,
                pub_bye=pub_bye, root_bye=root_bye)


def compare(d: dict) -> tuple[list[dict], dict]:
    pub_index = {(r["team"], norm_name(r["player"])): r for r in d["pub"]}
    off_keys = set()
    rows = []
    for r in d["off"]:
        club = CODE_MAP.get(r["team_official"], r["team_official"])
        key = (club, norm_name(r["player"]))
        off_keys.add(key)
        p = pub_index.get(key)
        if p is None:
            status = "missing from published"
            pub_vals = {"practice_status": "", "game_status": "", "injury": "", "read_by": ""}
        else:
            pub_vals = {"practice_status": p["practice_status"], "game_status": p["game_status"],
                        "injury": p["injury"], "read_by": p["read_by"]}
            same = (p["injury"].strip() == r["injury"].strip()
                    and p["practice_status"].strip() == r["practice_status"].strip()
                    and p["game_status"].strip() == r["game_status"].strip()
                    and p["position"].strip() == r["position"].strip())
            status = "identical" if same else "differs"
        if p is None:
            read_label = "not in published table"
        elif "e46fb855" in p["read_by"]:
            read_label = "re-read 2026-11-15 (e46fb855)"
        else:
            read_label = "carried forward from earlier read"
        rows.append({
            "club_official": r["team_official"],
            "club": club,
            "player": r["player"],
            "position": r["position"],
            "official_injury": r["injury"],
            "official_practice_status": r["practice_status"],
            "official_game_status": r["game_status"],
            "published_injury": pub_vals["injury"],
            "published_practice_status": pub_vals["practice_status"],
            "published_game_status": pub_vals["game_status"],
            "published_read": read_label,
            "row_status": status,
            "source_url": r["source_url"],
        })
    published_only = [r for r in d["pub"] if (r["team"], norm_name(r["player"])) not in off_keys]
    summary = {
        "official_rows": len(d["off"]),
        "official_clubs": len({CODE_MAP.get(r["team_official"], r["team_official"]) for r in d["off"]}),
        "published_rows": len(d["pub"]),
        "published_only_rows": len(published_only),
        "identical": sum(1 for r in rows if r["row_status"] == "identical"),
        "differs": sum(1 for r in rows if r["row_status"] == "differs"),
        "missing_from_published": sum(1 for r in rows if r["row_status"] == "missing from published"),
        "published_rows_carried_forward": sum(1 for r in d["pub"] if "e46fb855" not in r["read_by"]),
        "published_rows_reread_e46": sum(1 for r in d["pub"] if "e46fb855" in r["read_by"]),
        "official_rows_with_game_status": sum(1 for r in d["off"] if r["game_status"].strip()),
        "published_rows_with_game_status": sum(1 for r in d["pub"] if r["game_status"].strip()),
        "official_rows_with_injury_text": sum(1 for r in d["off"] if r["injury"].strip()),
        "published_rows_with_injury_text": sum(1 for r in d["pub"] if r["injury"].strip()),
        "official_clubs_with_no_injury_text": 0,
        "official_clubs_playing_per_page": sorted({CODE_MAP.get(r["team_official"], r["team_official"]) for r in d["off"]}),
    }
    clubs_all = defaultdict(list)
    for r in d["off"]:
        clubs_all[CODE_MAP.get(r["team_official"], r["team_official"])].append(r)
    summary["official_clubs_with_no_injury_text"] = sum(
        1 for c, rs in clubs_all.items() if not any(x["injury"].strip() for x in rs))
    summary["official_rows_per_club"] = {c: len(clubs_all[c]) for c in sorted(clubs_all)}
    summary["official_byes_wk10"] = sorted(set(ALL_32) - set(clubs_all))
    return rows, summary


def run_checks(d: dict, rows: list[dict], s: dict) -> None:
    check(s["official_rows"] == EXPECTED_OFFICIAL_TOTAL,
          f"official row total is {EXPECTED_OFFICIAL_TOTAL} (found {s['official_rows']})")
    per = Counter(CODE_MAP.get(r["team_official"], r["team_official"]) for r in d["off"])
    mism = {c: (EXPECTED_OFFICIAL_PER_CLUB.get(next((k for k, v in CODE_MAP.items() if v == c), c), None), per.get(c, 0))
            for c in per
            if EXPECTED_OFFICIAL_PER_CLUB.get(next((k for k, v in CODE_MAP.items() if v == c), c), None) != per.get(c, 0)}
    check(not mism, f"per-club official counts match hand tally (mismatches: {mism})")
    check(s["official_clubs"] == 28, f"28 clubs appear on the Week 10 page (found {s['official_clubs']})")
    check(s["official_byes_wk10"] == sorted(EXPECTED_BYES_WK10),
          f"Week 10 byes derived from the page are {EXPECTED_BYES_WK10} (found {s['official_byes_wk10']})")
    check(len({(r['team_official'], r['player']) for r in d['off']}) == len(d['off']),
          "no duplicate (club, player) rows on the official page")
    check(s["identical"] + s["differs"] + s["missing_from_published"] == s["official_rows"],
          "every official row has exactly one status")
    matched = s["official_rows"] - s["missing_from_published"]
    check(matched == s["published_rows"] - s["published_only_rows"],
          "published rows reconcile: matched + published-only = published total")
    check(s["published_only_rows"] == 0, "no published row is absent from the official page")
    check(s["published_rows_reread_e46"] == 49, "49 published rows were re-read on 2026-11-15 (e46fb855)")
    reread_ok = all(r["row_status"] == "identical" for r in rows if r["published_read"].startswith("re-read"))
    check(reread_ok, "all 49 rows re-read on 2026-11-15 are identical to the 2026-11-17 official read")
    det = {r["player"]: r for r in d["off"] if r["team_official"] == "DET"}
    check(all(det[p]["game_status"] == "Out" for p in ["Kerby Joseph", "Cade Mays", "D.J. Reed"]),
          "Lions: Kerby Joseph, Cade Mays and D.J. Reed are Out on the official page")
    check(s["official_rows_per_club"].get("SEA") == 15, "Seattle has 15 official rows")
    check(s["official_rows_per_club"].get("CIN") == 9, "Cincinnati has 9 official rows")
    check(all(r["source_url"].startswith("https://www.nfl.com/") for r in d["off"]),
          "every official row carries an nfl.com source URL")
    check(all(r["source_url"].startswith("https://www.nfl.com/") for r in d["tx"]),
          "every transaction row carries an nfl.com source URL")
    check(all(r["source_url"].startswith("https://") for r in d["claims"] if r["source_url"]),
          "every claim row carries an https source URL")
    check(all(r["source_url"].startswith("https://") for r in d["flags"]),
          "every flagged row carries an https source URL")
    check(any(r["name"] == "Malik Willis" for r in d["tx"]) and
          not any(r["player"] == "Malik Willis" for r in d["off"] if r["team_official"] == "MIA"),
          "Malik Willis: on the reserve list and absent from the Dolphins' Week 10 rows")
    check(sorted(r["name"] for r in d["tx"] if r["record_type"] == "trade" and r["from_club"].startswith("Colts"))
          == ["Josh Downs", "Keenan Allen"],
          "Colts: Keenan Allen and Josh Downs traded from IND (trades log)")
    henley_off = [r for r in d["off"] if r["player"] == "Daiyan Henley"]
    henley_tx = [r for r in d["tx"] if r["name"] == "Daiyan Henley"]
    check(bool(henley_off) and henley_off[0]["team_official"] == "LAC" and henley_tx and "Broncos" in henley_tx[0]["to_club"],
          "Henley conflict is as recorded: listed under LAC on the report; traded to DEN on the log")
    pub_w10_byes = [t for t in re.split(r"\s+", next((r["teams_on_bye"] for r in d["pub_bye"] if r["week"] == "10"), "")) if t]
    check(sorted(pub_w10_byes) != sorted(EXPECTED_BYES_WK10),
          "published desk bye file for Week 10 differs from the official bye set (expected: known error)")
    root_w10 = next((r["teams_on_bye"] for r in d["root_bye"] if r["week"] == "10"), "")
    check(all(t in root_w10 for t in ["Chicago Bears", "Denver Broncos", "Philadelphia Eagles", "Tampa Bay Buccaneers"])
          and root_w10.count(";") == 3,
          "root bye file lists exactly CHI, DEN, PHI, TB for Week 10")


# ----------------------------------------------------------------------------
# HTML
# ----------------------------------------------------------------------------

CSS = """
:root{--ink:#1d2430;--mute:#5b6675;--line:#dfe4ea;--bg:#f7f9fb;--card:#fff;--ok:#1d7a4a;--bad:#b42318;--warn:#8a5a00;--acc:#0b5cad}
*{box-sizing:border-box}body{margin:0;font:15px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;color:var(--ink);background:var(--bg)}
header{background:#14213d;color:#fff;padding:18px 24px}header h1{margin:0;font-size:20px}header p{margin:4px 0 0;color:#c9d3e3;font-size:13px}
nav{background:#fff;border-bottom:1px solid var(--line);padding:0 24px;display:flex;gap:18px;flex-wrap:wrap}
nav a{display:inline-block;padding:12px 0;color:var(--acc);text-decoration:none;font-weight:600;font-size:14px}nav a.on{color:var(--ink);border-bottom:3px solid var(--acc)}
main{padding:20px 24px;max-width:1400px;margin:0 auto}h2{font-size:17px;margin:26px 0 8px}h3{font-size:15px;margin:18px 0 6px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin:14px 0}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px 14px}.kpi b{display:block;font-size:24px}.kpi span{color:var(--mute);font-size:13px}
.verdict{background:#fff7e6;border:1px solid #f1d28a;border-radius:8px;padding:12px 16px;margin:12px 0}
.note{color:var(--mute);font-size:13px}
.tablewrap{overflow:auto;background:var(--card);border:1px solid var(--line);border-radius:8px;margin:8px 0}
table{border-collapse:collapse;width:100%;font-size:13px}th,td{padding:7px 9px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{background:#eef2f7;position:sticky;top:0;font-weight:600;z-index:1}tr:hover td{background:#fbfcfe}
.tag{display:inline-block;border-radius:4px;padding:1px 7px;font-size:12px;font-weight:600;white-space:nowrap}
.t-identical,.t-ok{background:#e6f4ec;color:var(--ok)}.t-differs,.t-bad{background:#fdecea;color:var(--bad)}
.t-missing{background:#fdf3e1;color:var(--warn)}.t-conf,.t-warn{background:#fff3cd;color:var(--warn)}.t-info{background:#e8f0fb;color:var(--acc)}
.blank{color:#9aa3af;font-style:italic}a{color:var(--acc)}
.filters{display:flex;gap:10px;flex-wrap:wrap;margin:8px 0}.filters input,.filters select{padding:6px 9px;border:1px solid #c8d0da;border-radius:6px;font-size:13px}
footer{color:var(--mute);font-size:12px;padding:20px 24px;max-width:1400px;margin:0 auto}
"""

NAV = [("index.html", "Overview"), ("comparison.html", "Week 10 row check"),
       ("transactions.html", "Official transactions"), ("flagged.html", "Flagged for Review")]


def page(title: str, active: str, body: str, subtitle: str) -> str:
    links = "".join(f'<a href="{href}"{" class=on" if href == active else ""}>{esc(label)}</a>' for href, label in NAV)
    links += f'<a href="{MAIN_DESK}">Main desk (e46fb855)</a>'
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} — Own5 NFL audit (a699fc53)</title><style>{CSS}</style></head>
<body><header><h1>{esc(title)}</h1><p>{esc(subtitle)}</p></header>
<nav>{links}</nav><main>{body}</main>
<footer>Own5 NFL audit a699fc53. Every table row links to an official nfl.com page. Blank cells are blank because no official value was found; nothing is inferred.
Source of record: <a href="https://www.nfl.com/injuries/league/2026/reg10">nfl.com Week 10 injury report</a>.</footer></body></html>"""


def tag(status: str) -> str:
    cls = {"identical": "t-identical", "differs": "t-differs", "missing from published": "t-missing"}.get(status, "t-info")
    return f'<span class="tag {cls}">{esc(status)}</span>'


def verdict_tag(v: str) -> str:
    u = v.upper()
    if u.startswith("CONFIRMED") or u.startswith("RESOLVED"):
        cls = "t-ok"
    elif u.startswith("CONTRADICTED") or u.startswith("CONFLICT") or u.startswith("ERROR"):
        cls = "t-bad"
    elif u.startswith("UNVERIFIED") or u.startswith("PARTIAL") or u.startswith("NOT"):
        cls = "t-warn"
    else:
        cls = "t-info"
    return f'<span class="tag {cls}">{esc(v)}</span>'


def sev_tag(sev: str) -> str:
    cls = {"high": "t-bad", "medium": "t-warn", "review": "t-info"}.get(sev.strip().lower(), "t-info")
    return f'<span class="tag {cls}">{esc(sev)}</span>'


def link(url: str, text: str | None = None) -> str:
    return f'<a href="{esc(url)}" rel="noopener">{esc(text or url)}</a>'


def build_index(s: dict, claims: list[dict]) -> str:
    kp = [
        (s["official_rows"], "official rows on the live Week 10 report"),
        (s["published_rows"], "rows in the published desk table"),
        (s["missing_from_published"], "official rows absent from the published table"),
        (s["differs"], "published rows that differ from the official page"),
        (f'{s["official_rows_with_game_status"]} vs {s["published_rows_with_game_status"]}', "game-status designations: official vs published"),
        (s["published_rows_carried_forward"], "published rows carried forward from an earlier read"),
    ]
    kpis = "".join(f'<div class="kpi"><b>{esc(str(v))}</b><span>{esc(t)}</span></div>' for v, t in kp)
    rows = ""
    for c in claims:
        rows += (f"<tr><td>{esc(c['id'])}</td><td>{esc(c['brief_item'])}</td>"
                 f"<td>{esc(c['claim_as_written'])}</td><td>{esc(c['official_evidence_read_2026_11_17'])}</td>"
                 f"<td>{verdict_tag(c['verdict'])}</td><td>{link(c['source_url'])}</td></tr>")
    claims_table = ('<div class="tablewrap"><table><thead><tr><th>ID</th><th>Brief item</th><th>Claim as written</th>'
                    '<th>What the official page shows (read 2026-11-17)</th><th>Verdict</th><th>Official source</th></tr></thead>'
                    f'<tbody>{rows}</tbody></table></div>')
    body = f"""
<h2>Summary</h2>
<div class="verdict"><b>Verdict:</b> the published Week 10 injury table on the main desk is stale. It must not be used as a model input until it is re-published from the {s['official_rows']}-row re-capture in this desk. The Lions game-status gap is fixed on main. Cincinnati's count, the Week 10 bye file and the game-status coverage are not.</div>
<div class="kpis">{kpis}</div>
<p class="note">Captured from nfl.com on 2026-11-17, before 00:40Z. The page is a live report, so these numbers are a dated snapshot. Week 11's report was not yet published at capture.</p>

<h2>Brief claims checked against official pages</h2>
<p class="note">One row per claim. Verdicts: CONFIRMED / RESOLVED mean the official page supports the claim. CONTRADICTED / CONFLICT mean it does not. UNVERIFIED / NOT CHECKED mean this session did not find the evidence, so nothing is asserted.</p>
{claims_table}

<h2>How the row check was done</h2>
<ol>
<li>All eight pages of the live Week 10 report were read through the sandbox page fetcher (nfl.com cannot be reached with curl from the sandbox). The page text was transcribed row by row into <code>data/official_injury_report_wk10_2026.csv</code>.</li>
<li>Club counts were tallied by hand before the transcription was compared with the published table. The build asserts that the counts match the tally club by club.</li>
<li>The 49 rows the previous desk re-read on 2026-11-15 were compared against this read: 49 of 49 are identical. This is the cross-check on the transcription.</li>
<li>Each published row was matched to the official row on club and player name, then compared on injury, practice status, game status and position. Result per row is on the <a href="comparison.html">Week 10 row check</a> page.</li>
<li>Transactions were read from the official trades and reserve-list pages for November 2026 and October 2026 (the October capture shows 10/24–10/31 only). See <a href="transactions.html">Official transactions</a>.</li>
</ol>

<h2>What this desk cannot verify yet</h2>
<ul>
<li>No market prices, no game books, no official inactive lists, no snap counts. These are outside what was read here.</li>
<li>No dated depth-chart capture for any club in this session. Houston and Packers depth items are not checked.</li>
<li>Reserve-list history is only partly visible (see Flagged F05–F06). A "not listed" entry is not treated as "available".</li>
</ul>
<p class="note">Nothing on this site is a betting recommendation. The purpose is data quality: which published values match the official source, and which do not.</p>
"""
    return page("Week 10 official re-read — overview", "index.html", body,
                "Own5 · NFL · official-source re-read, 2026-11-17 UTC · Week 10 injury report (2026 season)")


def build_comparison(rows: list[dict], s: dict) -> str:
    head = ("<tr><th>Club</th><th>Player</th><th>Pos</th><th>Official injury</th><th>Official practice</th>"
            "<th>Official game status</th><th>Published practice</th><th>Published game status</th>"
            "<th>Published row</th><th>Row status</th><th>Source</th></tr>")
    body_rows = []
    for r in rows:
        assert r["source_url"].startswith("https://www.nfl.com/"), r
        body_rows.append(
            f"<tr data-status=\"{esc(r['row_status'])}\" data-text=\"{esc((r['club']+' '+r['player']).lower())}\">"
            f"<td>{esc(r['club'])}</td><td>{esc(r['player'])}</td><td>{esc(r['position'])}</td>"
            f"<td>{fmt_blank(r['official_injury'])}</td><td>{fmt_blank(r['official_practice_status'])}</td>"
            f"<td>{fmt_blank(r['official_game_status'])}</td>"
            f"<td>{fmt_blank(r['published_practice_status'])}</td><td>{fmt_blank(r['published_game_status'])}</td>"
            f"<td>{esc(r['published_read'])}</td><td>{tag(r['row_status'])}</td>"
            f"<td>{link(r['source_url'], 'nfl.com Week 10 report')}</td></tr>")
    script = """<script>
const q=document.getElementById('q'),st=document.getElementById('st');
function f(){const t=q.value.toLowerCase(),s=st.value;
document.querySelectorAll('tbody tr').forEach(r=>{const ok=(!t||r.dataset.text.includes(t))&&(!s||r.dataset.status===s);r.style.display=ok?'':'none';});}
q.addEventListener('input',f);st.addEventListener('change',f);
</script>"""
    body = f"""
<h2>Official Week 10 rows against the published table</h2>
<p class="note">Each row is one official row from the live page, matched to the published table on club and player. "Official" columns are the page. "Published" columns are the main desk's injuries.csv. Blank is shown as <span class="blank">blank</span> and means no value in that source.</p>
<div class="kpis">
<div class="kpi"><b>{s['identical']}</b><span>identical on all fields</span></div>
<div class="kpi"><b>{s['differs']}</b><span>present but differ</span></div>
<div class="kpi"><b>{s['missing_from_published']}</b><span>missing from the published table</span></div>
<div class="kpi"><b>{s['official_rows_with_game_status']}</b><span>official rows with a game status</span></div>
<div class="kpi"><b>{s['published_rows_with_game_status']}</b><span>published rows with a game status</span></div>
</div>
<div class="filters"><input id="q" type="search" placeholder="Filter club or player"><select id="st">
<option value="">All statuses</option><option value="identical">identical</option><option value="differs">differs</option>
<option value="missing from published">missing from published</option></select></div>
<div class="tablewrap"><table><thead>{head}</thead><tbody>{''.join(body_rows)}</tbody></table></div>
{script}
"""
    return page("Week 10 row check", "comparison.html", body,
                f"{s['official_rows']} official rows · {s['published_rows']} published rows · official read 2026-11-17 (before 00:40Z)")


def build_transactions(tx: list[dict]) -> str:
    trades = [r for r in tx if r["record_type"] == "trade"]
    reserve = [r for r in tx if r["record_type"] == "reserve"]
    t_rows = "".join(
        f"<tr><td>{esc(r['date_2026'])}</td><td>{esc(r['name'])}</td><td>{esc(r['from_club'])}</td><td>{esc(r['to_club'])}</td>"
        f"<td>{esc(r['transaction'])}</td><td>{link(r['source_url'], 'nfl.com trades, Nov 2026')}</td></tr>" for r in trades)
    r_rows = "".join(
        f"<tr><td>{esc(r['date_2026'])}</td><td>{esc(r['name'])}</td><td>{esc(r['from_club'])}</td>"
        f"<td>{esc(r['transaction'])}</td><td>{link(r['source_url'], 'nfl.com reserve list, Nov 2026')}</td></tr>" for r in reserve)
    body = f"""
<h2>Official trades, November 2026 (captured 2026-11-17)</h2>
<p class="note">Trades only; roster moves to injured reserve are in the next table. Dates are as printed on the official page (MM/DD).</p>
<div class="tablewrap"><table><thead><tr><th>Date</th><th>Name</th><th>From</th><th>To</th><th>Transaction</th><th>Source</th></tr></thead><tbody>{t_rows}</tbody></table></div>
<h2>Official reserve list entries visible in the November capture (11/07–11/16)</h2>
<p class="note">The page shows only this window. Earlier November or October entries are not in the capture, so "not listed" is not treated as "available". The October capture (10/24–10/31) did not show Lamar Jackson or Tyler Huntley; see Flagged F05.</p>
<div class="tablewrap"><table><thead><tr><th>Date</th><th>Name</th><th>Club</th><th>Transaction</th><th>Source</th></tr></thead><tbody>{r_rows}</tbody></table></div>
"""
    return page("Official transactions", "transactions.html", body,
                "Official nfl.com trades and reserve-list pages, read 2026-11-17 UTC")


def build_flagged(flags: list[dict]) -> str:
    rows = "".join(
        f"<tr><td>{esc(f['id'])}</td><td>{sev_tag(f['severity'])}</td><td>{esc(f['area'])}</td>"
        f"<td>{esc(f['what_is_flagged'])}</td><td>{esc(f['evidence'])}</td>"
        f"<td>{link(f['source_url'])}</td><td>{esc(f['action_requested'])}</td></tr>" for f in flags)
    body = f"""
<h2>Flagged for Review</h2>
<p class="note">Non-blocking. Each item is published with its official source so it can be checked and a change can be requested. Severity: high = a published value is wrong or a source conflicts; medium = a gap that limits a claim; review = a limit of method or scope.</p>
<div class="tablewrap"><table><thead><tr><th>ID</th><th>Severity</th><th>Area</th><th>What is flagged</th><th>Evidence</th><th>Official source</th><th>Action requested</th></tr></thead><tbody>{rows}</tbody></table></div>
<h2>Cross-session requests (not actioned here)</h2>
<ul>
<li><b>R-a699-1</b> — <code>nfl-desk-e46fb855/data/injuries.csv</code> should be re-published from <code>nfl-audit-a699fc53/data/official_injury_report_wk10_2026.csv</code>. Owner: e46fb855 (finished; no edit made).</li>
<li><b>R-a699-2</b> — <code>nfl-desk-e46fb855/data/bye_weeks_2026.csv</code> Week 10 row should read CHI, DEN, PHI, TB. Owner: e46fb855 (finished; no edit made).</li>
</ul>
"""
    return page("Flagged for Review", "flagged.html", body,
                "Irregularities, unverified items and open cross-session requests · all linked to official sources")


# ----------------------------------------------------------------------------
# Checks on generated HTML
# ----------------------------------------------------------------------------

def check_html(pages: dict[str, str]) -> None:
    for name, text in pages.items():
        hrefs = re.findall(r'href="([^"]+)"', text)
        internal = [h for h in hrefs if not h.startswith(("http://", "https://", "#"))]
        bad = []
        for h in internal:
            path = h.split("#")[0]
            if not path:
                continue
            if path in pages:
                continue
            target = (HERE / path) if not path.startswith("../") else (ROOT / path[3:])
            if not target.exists():
                bad.append(h)
        check(not bad, f"{name}: every internal link resolves ({bad or 'ok'})")
    comp = pages["comparison.html"]
    trs = re.findall(r"<tbody>(.*)</tbody>", comp, re.S)[0]
    body_rows = re.findall(r"<tr data-status", trs)
    check(len(body_rows) == EXPECTED_OFFICIAL_TOTAL,
          f"comparison page renders {EXPECTED_OFFICIAL_TOTAL} rows (found {len(body_rows)})")
    check(len(re.findall(r'href="https://www\.nfl\.com/', comp)) >= EXPECTED_OFFICIAL_TOTAL,
          "every comparison row carries an nfl.com link")


def main(argv: list[str]) -> int:
    d = load()
    rows, s = compare(d)
    run_checks(d, rows, s)
    if FAILURES:
        print(f"\n{len(FAILURES)} check(s) failed; not writing pages.")
        return 1
    # Write the derived files only after every source check has passed.
    with (DATA / "comparison_wk10.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    (DATA / "summary.json").write_text(json.dumps(s, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    pages = {
        "index.html": build_index(s, d["claims"]),
        "comparison.html": build_comparison(rows, s),
        "transactions.html": build_transactions(d["tx"]),
        "flagged.html": build_flagged(d["flags"]),
    }
    if "--check" in argv:
        check_html(pages)
    else:
        for name, text in pages.items():
            (HERE / name).write_text(text, encoding="utf-8")
        check_html(pages)
    if FAILURES:
        print(f"\n{len(FAILURES)} check(s) failed.")
        return 1
    print("\nALL CHECKS PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

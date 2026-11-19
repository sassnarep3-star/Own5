"""Build the brief-traceability matrix (session 1911d7cd).

Statuses are read from nfl-line-audit/data/requirements.csv at build time, never typed.
Only the 'this_session_check' column is written by hand, and only for items this session
actually re-checked (see reproduce.log, spotcheck_wk11.csv and flags.csv).
"""
import csv, html, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
REG = os.path.join(ROOT, "nfl-line-audit/data/requirements.csv")
REPO = "https://github.com/sassnarep3-star/Own5/blob/main/"
OFFICIAL_WK11 = "https://www.nfl.com/injuries/league/2026/reg11"

# (brief item in the user's own words, register id or None, this-session check, note, official link or '')
# this-session check: PASS = re-verified now; FAIL = irregularity found now; NOT CHECKED = register claim not re-read here.
ITEMS = [
    ("Price-snapshot store: opening and closing numbers for every market originated", "R01", "NOT CHECKED", "Closings are pending kickoff; not re-read here.", ""),
    ("Verified results feed so backtests and ROI can be computed", "R02", "NOT CHECKED", "", ""),
    ("Originate the side first, then the total, then the moneyline", "R03", "NOT CHECKED", "", ""),
    ("Publish fair line, market line and difference as separate columns", "R04", "NOT CHECKED", "", ""),
    ("Separate signal from staking in the leaderboard", "R05", "NOT CHECKED", "", ""),
    ("Track depth of the replacement, not just the fact of a replacement", "R06", "NOT CHECKED", "", ""),
    ("Correlations only from officially sourced numbers, with n", "R07", "NOT CHECKED", "Register classes some coefficients as PINNED-DATASET, not OFFICIAL.", ""),
    ("Demotion gate that sends a live strategy back to paper", "R08", "NOT CHECKED", "", ""),
    ("Pre-register every strategy; no backtest numbers on the leaderboard", "R09", "PASS", "Registration hash recomputed by verify.py (80/80 checks pass, reproduce.log).", ""),
    ("Availability graph as a first-class dataset (expected vs actual starters)", "R10", "FAIL", "Row and club counts in the register (253 rows, 24 clubs) do not match the file (255 rows, 26 clubs). 'Actual' side is playing time from a non-official feed. See F-B02.", OFFICIAL_WK11),
    ("Depth from playing time, never from jersey order", "R11", "NOT CHECKED", "Usage rule itself not re-audited here.", ""),
    ("Injury signal is a surprise (delta), never a level", "R12", "NOT CHECKED", "", ""),
    ("32-team roster/IR sweep before any team-level model is trusted", "R13", "NOT CHECKED", "Register itself says completeness across 32 clubs is not established.", ""),
    ("Fixture-context features built only from published schedule facts", "R14", "NOT CHECKED", "", ""),
    ("Store every model output as a probability plus its inputs", "R15", "NOT CHECKED", "", ""),
    ("Removal-of-luck panel on the dashboard", "R16", "NOT CHECKED", "", ""),
    ("Two-sided 'what would change our mind' on every strategy entry", "R17", "NOT CHECKED", "", ""),
    ("Price our own line; publish residual vs market on a schedule", "R18", "NOT CHECKED", "", ""),
    ("Turn the 136-game log into the pre-registered backtest corpus", "R19", "NOT CHECKED", "", ""),
    ("Decide the price-data policy before any backtest is published", "R20", "NOT CHECKED", "", ""),
    ("Store every injury-hub read with its clock time; publish the delta, never the level", "R21", "NOT CHECKED", "", ""),
    ("Decision-readiness table on the landing page", "R22", "NOT CHECKED", "The desk page carries a 71-row table. The Pages root notice cites a '78-row' table, which does not match the register (see F-B06).", ""),
    ("Transcribe venue of every fixture from the official game centre", "R23", "NOT CHECKED", "", ""),
    ("Publish dated schedule announcement beside the live schedule page", "R24", "NOT CHECKED", "", ""),
    ("Use official NFL Game Books for actual starters and game-day status", "R25", "NOT CHECKED", "Register says NOT MET.", ""),
    ("Ingest game-level results to make ratings opponent-aware", "R26", "NOT CHECKED", "", ""),
    ("Injury and personnel ablations instead of fixed penalties", "R27", "NOT CHECKED", "", ""),
    ("Immutable multi-day availability snapshots with retained hashes (daily)", "R28", "NOT CHECKED", "Register says the workflow is committed but this session's reads are text-level.", ""),
    ("Capture official inactive lists and snap counts", "R29", "NOT CHECKED", "Register says no official inactive list was read.", ""),
    ("Fix the two depth-parsing failures (Texans image; Packers jersey prefixes)", "R30", "NOT CHECKED", "Register says NOT MET.", ""),
    ("Model depth slots as groups, not a single starter", "R31", "NOT CHECKED", "", ""),
    ("Roster turnover as a first-class data event (Colts Week 10 receiver trades)", "R32", "NOT CHECKED", "", ""),
    ("Singles-only shadow baseline, frozen before kickoff", "R33", "NOT CHECKED", "", ""),
    ("Parlays and prop combos behind a joint-evidence gate", "R34", "NOT CHECKED", "", ""),
    ("Proper-score leaderboard divisions (singles, parlays, SGP, props)", "R35", "NOT CHECKED", "", ""),
    ("Rank by proper score with uncertainty, not win rate", "R36", "NOT CHECKED", "", ""),
    ("Durable snapshot storage outside the static site, with alerts", "R37", "NOT CHECKED", "Register: no external store configured.", ""),
    ("Split site into public analysis layer and private raw-data layer", "R38", "NOT CHECKED", "", ""),
    ("Per-team view: starters out, replacements named, net injury count", "R39", "NOT CHECKED", "", ""),
    ("Announced-starter evidence field (dated starter changes, not inferred replacements)", "R40", "NOT CHECKED", "Register says NOT MET (Lock, McCord, Brissett cases not yet in the register).", ""),
    ("Official depth-chart register with date and source per row", "R41", "NOT CHECKED", "Register says NOT MET.", ""),
    ("Calibrate what 'Questionable' means empirically", "R42", "NOT CHECKED", "", ""),
    ("Interactive offense vs defense matchup deficiency matrix (1st–4th string)", "R43", "NOT CHECKED", "Register says NOT MET.", ""),
    ("Flag stale depth rows against the official transactions log (Baltimore QB rows)", "R44", "NOT CHECKED", "Register says NOT MET.", ""),
    ("Point-in-time snapshot ledger for injuries, depth charts and inactives", "R45", "NOT CHECKED", "", ""),
    ("Populate the missing game-status designations (Lions, Week 10)", "R46", "FAIL", "Count in the register (253 row entries) is wrong: file has 255 rows. The 16 populated game-status cells (9 Out, 7 Questionable) do match. The Week 10 Lions cells were not re-read here. See F-B03.", ""),
    ("Re-capture and republish the Week 10 injury tables (254→279 rows)", None, "NOT CHECKED", "No register row. Week 10 is superseded by the Week 11 capture; the Week 10 publication should be checked for staleness.", ""),
    ("Reject deriving depth from jersey number, experience or salary", "R47", "NOT CHECKED", "", ""),
    ("Represent shared and empty depth slots faithfully (Seattle, Washington)", "R48", "NOT CHECKED", "", ""),
    ("Resolve depth-order source (route a: club depth pages; route b: official snap counts) before the backup feature", "R49", "FAIL", "Marked MET, but the route used is playing time from nflverse snap counts, which the register's own source table classes AGGREGATOR (SRC11). The brief's route (b) requires an official snap-count source, and route (a) is not verified for 32 clubs. Status should not be MET. See F-B04.", ""),
    ("Score injury-designation reliability before using it as a feature", "R50", "NOT CHECKED", "", ""),
    ("Snapshot the injury report every Wed, Thu and Fri, dated", "R51", "NOT CHECKED", "", ""),
    ("Treat the injury report as a timestamped series (DNP→LP→FP, Questionable→Out)", "R52", "NOT CHECKED", "", ""),
    ("Use snap counts as the starter proxy when the depth chart is unavailable", "R53", "NOT CHECKED", "Snap counts are from an AGGREGATOR source (see F-B04).", ""),
    ("Control baselines (random picks; favourites only) on every leaderboard run", "R54", "NOT CHECKED", "", ""),
    ("Stadium roof/surface and hourly wind/precipitation overlay", "R55", "NOT CHECKED", "Register says NOT MET.", ""),
    ("Two-stage skill leaderboard (proper-score qualification, then prospective CLV/ROI escrow)", "R56", "NOT CHECKED", "", ""),
    ("Vig-free market consensus vs originated fair-line decomposition", "R57", "NOT CHECKED", "", ""),
    ("Weekly 'what changed' diff instead of a static snapshot", "R58", "NOT CHECKED", "", ""),
    ("Publish every model total twice until one wins", "R59", "NOT CHECKED", "Register says NOT MET.", ""),
    ("Drift alarm on every scraper (pinned row counts; fail loudly)", "R60", "FAIL", "Verifier runs and passes (80/80), but this row's source link points to a path that does not exist (nfl-line-audit/data/nfl-line-audit/verify.py). See F-B01.", ""),
    ("Capture the reserve list so 'not listed' never means 'available' (Malik Willis, IR)", "R61", "NOT CHECKED", "", ""),
    ("Archive weekly injury reports for past seasons", "R62", "NOT CHECKED", "Register says the archive is from an aggregator, not an official archive.", ""),
    ("Pre-register each strategy with its definition frozen before results", "R63", "PASS", "Registration hash recomputed by verify.py.", ""),
    ("2026 kickoff and declared onside-kick regime priors filter", "R64", "NOT CHECKED", "Register says NOT MET.", ""),
    ("Freeze a rule before it sees data; the commit hash is the registration", "R65", "PASS", "Registration hash recomputed by verify.py.", ""),
    ("Split data into train, validation and final holdout seasons", "R66", "NOT CHECKED", "", ""),
    ("Suggestions section so the best path is chosen before changes are made", "R67", "NOT CHECKED", "", ""),
    ("Questions register: what is known, what is missing, the answer", "R68", "NOT CHECKED", "", ""),
    ("Every table row links to an official source, or is blank and flagged", "R69", "FAIL", "Source link for this row is broken (F-B01). Across all 71 register rows, every source link points to a repository file, not to an official NFL page (F-B05).", ""),
    ("Executive summary restating only computed numbers", "R70", "NOT CHECKED", "", ""),
    ("Flag irregularities for review instead of hiding them", "R71", "NOT CHECKED", "This session added flags F-B01 to F-B09 (flags.csv).", ""),
    ("Site: clean landing page with category subpages, readable by a non-analyst", None, "FAIL", "The Pages root landing page is the stale 2026-11-02 research workspace (F-B06). It still says '78-row' readiness and '08 strategies'. The current desk is in /nfl-line-audit/.", ""),
    ("Reject ranking strategies by season-long ROI (SG-03)", None, "NOT CHECKED", "No register row found in nfl-line-audit/data/requirements.csv.", ""),
]

SPOT = [
    ("Official Week 11 injury report, IND and HOU rows (26 rows), read via nfl.com/injuries", "PASS 25/26; 1 name mismatch", "Repo capture 'Jake Hummel' vs official display 'Jacob Hummel' (F-B07). All other 25 rows match on injury, practice status and game status. Full row table: official_wk11_IND_HOU.csv and spotcheck_wk11.csv.", OFFICIAL_WK11),
    ("Deterministic rebuild of nfl-line-audit (build_data, build_registers, build_site)", "PASS", "Zero tracked-file diffs after rebuild; headline Brier skill −0.07815; verify.py 80/80. See reproduce.log.", ""),
]


def load_register():
    with open(REG, encoding="utf-8") as f:
        return {r["id"]: r for r in csv.DictReader(f)}


def build():
    reg = load_register()
    rows = []
    for i, (item, rid, check, note, official) in enumerate(ITEMS, 1):
        r = reg.get(rid) if rid else None
        rows.append({
            "no": i,
            "brief_item": item,
            "register_id": rid or "",
            "register_status": (r["status"] if r else "NOT IN REGISTER"),
            "register_blocking_gate": (r["blocking_gate"] if r else ""),
            "this_session_check": check,
            "this_session_note": note,
            "evidence_repo_path": (r["evidence_path"] if r else ""),
            "evidence_repo_link": (REPO + r["evidence_path"] if r else ""),
            "official_source_url": official,
        })
    return rows


def write_csv(rows):
    path = os.path.join(HERE, "brief_traceability.csv")
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    return path


def esc(s):
    return html.escape(str(s or ""))


def link(url, label=None):
    if not url:
        return '<span class="blank">BLANK — unverified</span>'
    return f'<a href="{esc(url)}">{esc(label or url)}</a>'


def write_html(rows):
    from collections import Counter
    st = Counter(r["register_status"] for r in rows if r["register_id"])
    chk = Counter(r["this_session_check"] for r in rows)
    flags = list(csv.DictReader(open(os.path.join(HERE, "flags.csv"), encoding="utf-8")))
    spot_rows = "".join(
        f"<tr><td>{esc(a)}</td><td><strong>{esc(b)}</strong></td><td>{esc(c)}</td><td>{link(d,'nfl.com')}</td></tr>"
        for a, b, c, d in SPOT)
    body_rows = []
    for r in rows:
        cls = {"PASS": "pass", "FAIL": "fail"}.get(r["this_session_check"], "nc")
        body_rows.append(
            f"<tr><td>{r['no']}</td><td>{esc(r['brief_item'])}</td>"
            f"<td>{esc(r['register_id']) or '—'}</td><td>{esc(r['register_status'])}</td>"
            f"<td class='{cls}'>{esc(r['this_session_check'])}</td>"
            f"<td>{esc(r['this_session_note'])}</td>"
            f"<td>{link(r['evidence_repo_link'], r['evidence_repo_path']) if r['evidence_repo_path'] else '—'}</td>"
            f"<td>{link(r['official_source_url'], 'nfl.com link' if r['official_source_url'] else None)}</td></tr>")
    flag_rows = "".join(
        f"<tr><td>{esc(f['id'])}</td><td>{esc(f['severity'])}</td><td>{esc(f['finding'])}</td>"
        f"<td>{link(f['source_url'], 'source')}</td></tr>" for f in flags)
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>NFL brief traceability · Own5</title>
<style>
body{{font-family:system-ui,-apple-system,Segoe UI,sans-serif;margin:0;background:#f6f7f9;color:#1d2530}}
header,main{{max-width:1280px;margin:0 auto;padding:20px}}
header{{background:#173e36;color:#fff}} header a{{color:#cfe9e1}}
h1{{margin:0 0 6px;font-size:26px}} h2{{margin-top:32px;font-size:20px}}
.cards{{display:flex;gap:12px;flex-wrap:wrap;margin:16px 0}}
.card{{background:#fff;border:1px solid #dde2e8;border-radius:8px;padding:12px 16px;min-width:150px}}
.card b{{display:block;font-size:22px}}
table{{width:100%;border-collapse:collapse;background:#fff;font-size:14px}}
th,td{{border-bottom:1px solid #e6e9ee;padding:8px;text-align:left;vertical-align:top}}
th{{background:#eef2f5;position:sticky;top:0}}
.pass{{color:#116b35;font-weight:600}} .fail{{color:#a11d1d;font-weight:600}} .nc{{color:#6b7280}}
.blank{{color:#9a6700;font-style:italic}}
.note{{background:#fff8e1;border:1px solid #f1d27a;border-radius:8px;padding:12px 16px}}
.wrap{{overflow-x:auto}}
</style></head><body>
<header><h1>NFL brief traceability</h1>
<div>Every item of the NFL brief, mapped to the register row that covers it, with this session's independent check. Session 1911d7cd, branch arena/1911d7cd-own5.</div>
<div><a href="../nfl-line-audit/">Desk home</a> · <a href="../nfl-line-audit/readiness.html">Readiness register</a> · <a href="../nfl-line-audit/flagged.html">Flagged desk</a></div></header>
<main>
<div class="note"><strong>Read this first.</strong> Statuses in the register column are copied from nfl-line-audit/data/requirements.csv at build time. The check column is what this session re-verified. FAIL means an irregularity was found. NOT CHECKED means the register claim was not re-read here. Nothing is marked verified unless it was checked against an official page. Flags and unverified items do not block publication.</div>
<div class="cards">
<div class="card"><span>Brief items mapped</span><b>{len(rows)}</b></div>
<div class="card"><span>Register MET / PARTIAL / NOT MET</span><b>{st.get('MET',0)} / {st.get('PARTIALLY MET',0)} / {st.get('NOT MET',0)}</b></div>
<div class="card"><span>Re-checked: PASS</span><b class="pass">{chk.get('PASS',0)}</b></div>
<div class="card"><span>Re-checked: FAIL</span><b class="fail">{chk.get('FAIL',0)}</b></div>
<div class="card"><span>Not re-checked here</span><b class="nc">{chk.get('NOT CHECKED',0)}</b></div>
</div>
<h2>Independent checks run this session</h2>
<div class="wrap"><table><thead><tr><th>Check</th><th>Result</th><th>Detail</th><th>Official link</th></tr></thead><tbody>{spot_rows}</tbody></table></div>
<h2>Brief items → register rows</h2>
<div class="wrap"><table><thead><tr><th>#</th><th>Brief item</th><th>Register</th><th>Register status</th><th>This session</th><th>Note</th><th>Repo evidence</th><th>Official source</th></tr></thead><tbody>{''.join(body_rows)}</tbody></table></div>
<h2>Flagged for review</h2>
<div class="wrap"><table><thead><tr><th>ID</th><th>Severity</th><th>Finding</th><th>Source</th></tr></thead><tbody>{flag_rows}</tbody></table></div>
</main></body></html>"""
    path = os.path.join(HERE, "index.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(page)
    return path


if __name__ == "__main__":
    rows = build()
    print(write_csv(rows))
    print(write_html(rows))

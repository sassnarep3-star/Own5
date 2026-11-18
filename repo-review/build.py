"""Build the repo-review data tables and pages from registers and the repository state.

Inputs : data/official_standings_2026_reg.csv, data/spot_checks.csv, data/irregularities.csv,
         data/verifier_runs.csv (from run_verifiers.py), the desk CSVs named below, git ls-files.
Outputs: data/inventory.csv, data/standings_check.csv, index.html, inventory.html,
         verifiers.html, spot-checks.html, flagged.html
Run    : python3 repo-review/build.py
"""
from __future__ import annotations

import csv
import html
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
DATA = HERE / "data"
GH = "https://github.com/sassnarep3-star/Own5"
LIVE = "https://sassnarep3-star.github.io/Own5"
DESK_E1 = REPO / "nfl-desk-e1d60f5d" / "data" / "standings_2026_wk11.csv"
HUB_RECON = REPO / "nfl-hub-28431d9c" / "data" / "reconcile_standings.csv"
DESK_LIST = REPO / "nfl-desk-5c5f4aaf" / "data" / "desks.csv"
PAGES_NAV = [
    ("index.html", "Overview"), ("inventory.html", "Inventory"), ("verifiers.html", "Verifiers"),
    ("spot-checks.html", "Official spot-checks"), ("flagged.html", "Flagged for Review"),
]
HUB = "../nfl-integration-a620f5a5/index.html"
AS_OF = "2026-11-18"


def esc(v: object) -> str:
    return html.escape(str(v), quote=True)


def read(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def link(url: str, label: str | None = None) -> str:
    if not url:
        return "<span class=\"blank\">blank</span>"
    return f'<a href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc(label or url)}</a>'


def badge(value: str) -> str:
    v = value.upper()
    cls = "ok" if v.startswith(("MATCH", "PASS", "FIXED")) else "bad" if v.startswith(("MISMATCH", "FAIL", "HIGH")) else "warn"
    return f'<span class="badge {cls}">{esc(value)}</span>'


def scope_of(name: str) -> str:
    if name.startswith("nba") or name == "docs":
        return "NBA (not NFL)"
    if name.startswith(("sf-rent", "rental")):
        return "San Francisco rent (not NFL)"
    if name.startswith("nfl") or name in {"line-lab", "own5-desk"}:
        return "NFL"
    if name == ".github":
        return "CI configuration"
    return "Shared site, data or tools"


def tracked_dirs() -> dict[str, int]:
    out = subprocess.run(["git", "ls-files"], cwd=REPO, capture_output=True, text=True, check=True).stdout.splitlines()
    counts: dict[str, int] = {}
    for path in out:
        top = path.split("/", 1)[0] if "/" in path else "(root file)"
        counts[top] = counts.get(top, 0) + 1
    return counts


def build_inventory() -> list[dict[str, str]]:
    runs = {r["directory"]: r for r in read("verifier_runs.csv")}
    counts = tracked_dirs()
    rows = []
    for name in sorted(k for k in counts if k not in {"(root file)"}):
        d = REPO / name
        if not d.is_dir():
            continue
        entry = ""
        for cand in ("index.html", "README.md"):
            if (d / cand).is_file():
                entry = cand
                break
        if not entry:
            htmls = sorted(p.name for p in d.glob("*.html"))
            entry = htmls[0] if htmls else ""
        live = f"{LIVE}/{name}/{entry}" if entry.endswith(".html") else ""
        run = runs.get(name)
        if name == "repo-review":
            verifier, result = "repo-review/verify.py", "RUN IN CI"
        else:
            verifier = f"{name}/verify.py" if run else ""
            result = run["result"] if run else "NO VERIFIER"
        rows.append({
            "directory": name,
            "scope": scope_of(name),
            "tracked_files": str(counts[name]),
            "entry_point": f"{name}/{entry}" if entry else "",
            "live_url": live,
            "verifier": verifier,
            "verifier_result": result,
            "workflow_files": run["workflow_files"] if run else "",
            "source_url": f"{GH}/tree/main/{name}",
        })
    return rows


def build_standings() -> list[dict[str, str]]:
    off = read("official_standings_2026_reg.csv")
    desk = {r["team"]: r for r in csv.DictReader(DESK_E1.open(encoding="utf-8"))}
    hub = {r["team"]: r for r in csv.DictReader(HUB_RECON.open(encoding="utf-8"))}
    out = []
    for o in off:
        t = o["team"]
        wlt = f"{o['official_w']}-{o['official_l']}-{o['official_t']}"
        pfpa = f"{o['official_pf']}/{o['official_pa']}"
        d = desk[t]
        dwlt = f"{d['wins']}-{d['losses']}-{d['ties']}"
        dpfpa = f"{d['pf']}/{d['pa']}"
        match_desk = (dwlt == wlt and dpfpa == pfpa)
        h = hub.get(t)
        hwlt = h["official_wlt"] if h else ""
        hpfpa = f"{h['official_pf']}/{h['official_pa']}" if h else ""
        match_hub = bool(h) and hwlt == wlt and hpfpa == pfpa
        out.append({
            "team": t, "official_wlt": wlt, "official_pf_pa": pfpa,
            "desk_e1d60f5d_wlt": dwlt, "desk_e1d60f5d_pf_pa": dpfpa,
            "result_desk_e1d60f5d": "MATCH" if match_desk else "MISMATCH",
            "hub_official_wlt_dated_2026_11_13": hwlt, "hub_official_pf_pa": hpfpa,
            "result_hub": "MATCH" if match_hub else "MISMATCH",
            "official_source_url": o["official_source_url"], "desk_source_url": f"{GH}/blob/main/nfl-desk-e1d60f5d/data/standings_2026_wk11.csv",
        })
    return out


def write_csv(name: str, rows: list[dict[str, str]]) -> None:
    with (DATA / name).open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def nav(current: str) -> str:
    items = []
    for href, label in PAGES_NAV:
        cls = " active" if href == current else ""
        items.append(f'<a class="nav-link{cls}" href="{href}">{esc(label)}</a>')
    items.append(f'<a class="nav-link" href="{HUB}">NFL integration hub ↗</a>')
    return "".join(items)


def page(title: str, current: str, body: str, lede: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{esc(lede)}">
  <title>{esc(title)} · Own5 repo review</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <a class="skip-link" href="#main">Skip to content</a>
  <header class="site-header">
    <a class="brand" href="index.html"><span class="brand-mark">O5</span><span>OWN5 <small>REPO REVIEW</small></span></a>
    <nav aria-label="Review navigation">{nav(current)}</nav>
    <span class="review-date">AS OF {AS_OF}</span>
  </header>
  <main id="main">
    <div class="page-title"><p class="eyebrow">REPOSITORY REVIEW · NFL · SPORTS RESEARCH</p><h1>{esc(title)}</h1><p>{esc(lede)}</p></div>
    {body}
  </main>
  <footer class="site-footer"><p>Independent research repository. Not affiliated with the NFL. No bets, no performance claims. Blank cells are unverified and flagged. Repo rows link to their file on GitHub; NFL facts link to nfl.com.</p></footer>
</body>
</html>
"""


def table(headers: list[str], rows: list[list[str]], caption: str) -> str:
    head = "".join(f"<th scope=\"col\">{esc(h)}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f"<section class=\"panel\"><div class=\"panel-head\"><h2>{esc(caption)}</h2><span>{len(rows)} rows</span></div><div class=\"table-wrap\"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div></section>"


def main() -> None:
    inventory = build_inventory()
    standings = build_standings()
    spots = read("spot_checks.csv")
    flags = read("irregularities.csv")
    runs = read("verifier_runs.csv")
    write_csv("inventory.csv", inventory)
    write_csv("standings_check.csv", standings)

    n_ver = len(runs)
    n_pass = sum(r["result"] == "PASS" for r in runs)
    n_fail = n_ver - n_pass
    by_scope: dict[str, int] = {}
    for r in inventory:
        by_scope[r["scope"]] = by_scope.get(r["scope"], 0) + 1
    n_nfl = by_scope.get("NFL", 0)
    n_nba = by_scope.get("NBA (not NFL)", 0)
    n_sf = by_scope.get("San Francisco rent (not NFL)", 0)
    sc_counts: dict[str, int] = {}
    for s in spots:
        key = s["result"].split(" (")[0]
        sc_counts[key] = sc_counts.get(key, 0) + 1
    st_match = sum(r["result_desk_e1d60f5d"] == "MATCH" for r in standings)
    hub_match = sum(r["result_hub"] == "MATCH" for r in standings)
    fixed = [f for f in flags if f["status"].startswith("FIXED")]
    open_high = [f for f in flags if not f["status"].startswith("FIXED") and f["severity"] == "HIGH"]

    stats = f"""
<section class="stats">
  <article><span>Desk verifiers run from the repo root</span><strong>{n_ver}</strong><small>{n_pass} PASS · {n_fail} FAIL after this session's fixes</small></article>
  <article><span>Top-level directories</span><strong>{len(inventory)}</strong><small>{n_nfl} NFL · {n_nba} NBA · {n_sf} San Francisco rent · the rest shared</small></article>
  <article><span>Official spot-checks</span><strong>{len(spots)}</strong><small>{sc_counts.get('MATCH', 0)} MATCH · {sc_counts.get('MISMATCH', 0)} MISMATCH · {sc_counts.get('NOT CHECKED', 0) + sc_counts.get('UNVERIFIED', 0)} NOT CHECKED or UNVERIFIED</small></article>
  <article><span>Team records vs 18 Nov official page</span><strong>{st_match}<em> / 32</em></strong><small>Desk capture 17 Nov matches on {st_match}; hub's 13 Nov read matches on {hub_match}</small></article>
  <article><span>Irregularities</span><strong>{len(flags)}</strong><small>{len(fixed)} fixed in this session · {len(flags) - len(fixed)} flagged for review</small></article>
</section>"""

    read_first = "".join(
        f"<li><strong>{esc(f['flag_id'])} · {esc(f['area'])}.</strong> {esc(f['observation'])} <a href=\"flagged.html#{esc(f['flag_id'].lower())}\">Details ↗</a></li>"
        for f in open_high
    )
    index_body = stats + f"""
<section class="panel brief"><div class="panel-head"><div><h2>What this review did</h2><p>Scope: the whole repository at branch arena/51cf3786-own5, base cb2d3b8.</p></div></div>
<ol class="steps">
  <li><strong>Ran every desk verifier</strong> from the repo root, the way the CI workflows do. Results are on the <a href="verifiers.html">verifiers page</a>.</li>
  <li><strong>Fixed two failing verifiers</strong> (RV-01, RV-02) with minimal changes; both now pass and are logged.</li>
  <li><strong>Checked official NFL pages line by line</strong> (Week 11 schedule and byes, Week 10 Lions designations (all 9 rows), Week 10 club coverage, all 32 team records). Results are on the <a href="spot-checks.html">spot-checks page</a>.</li>
  <li><strong>Recorded everything that could not be confirmed</strong> as a flagged item, with the evidence link and the action needed.</li>
</ol></section>
<section class="panel"><div class="panel-head"><div><h2>Read first: open high-severity items</h2><p>These are not blocking the merge. They are published for review.</p></div></div><ul class="readfirst">{read_first}</ul></section>
<section class="cards">
  <a class="card" href="inventory.html"><span>01</span><h3>Inventory</h3><p>Every top-level directory: scope, entry page, verifier result, source.</p></a>
  <a class="card" href="verifiers.html"><span>02</span><h3>Verifiers</h3><p>Exit code and summary line for each desk's verify.py.</p></a>
  <a class="card" href="spot-checks.html"><span>03</span><h3>Official spot-checks</h3><p>Desk values against nfl.com, with a 32-row standings table.</p></a>
  <a class="card" href="flagged.html"><span>04</span><h3>Flagged for Review</h3><p>All irregularities, with evidence links and actions.</p></a>
  <a class="card" href="{HUB}"><span>05</span><h3>NFL integration hub</h3><p>Questions, suggestions, sources, executive summary and decision readiness.</p></a>
</section>
<section class="panel scope"><h2>Scope and limits</h2><ul>
  <li>Official pages were read through the sandbox fetch tool on {AS_OF}. The tool returns a date, not a clock time, so each read is dated by day only.</li>
  <li>When read on 18 Nov, the official injury page still showed Week 10, so no Week 11 injury report was present (SC-04).</li>
  <li>Not re-verified here: the full 347-row Week 10 injury recount (RV-04), fixture venues (RV-05), and the other desks' row-level claims. Each desk's own verifier covers its own rows.</li>
  <li>This is a repository audit, not betting advice and not a performance claim. No strategy is validated here.</li>
</ul></section>"""
    (HERE / "index.html").write_text(page("Repo review", "index.html", index_body,
        "Line-by-line review of the Own5 repository: verifier runs, official spot-checks, inventory and flagged irregularities."), encoding="utf-8")

    inv_rows = []
    for r in inventory:
        inv_rows.append([
            esc(r["directory"]), esc(r["scope"]), esc(r["tracked_files"]),
            link(f"{LIVE}/{r['entry_point'][len(r['directory'])+1:]}" if r["entry_point"] else "", r["entry_point"]) if r["entry_point"] else "<span class=\"blank\">none</span>",
            badge(r["verifier_result"]), esc(r["workflow_files"]) or "<span class=\"blank\">none</span>",
            link(r["source_url"], "GitHub folder"),
        ])
    inv_body = (f"<p class=\"note\">Scope counts are computed from git ls-files. A folder is NFL when its name starts with nfl or is one of the NFL labs. "
                f"\"blank\" means the item does not exist in that folder.</p>"
                + table(["Directory", "Scope", "Tracked files", "Entry page", "Verifier", "Workflows that reference it", "Source"],
                        inv_rows, "Top-level directories"))
    (HERE / "inventory.html").write_text(page("Inventory", "inventory.html", inv_body,
        "Every top-level directory in the repository, classified by scope, with its entry page and verifier result."), encoding="utf-8")

    ver_rows = []
    for r in runs:
        ver_rows.append([
            esc(r["directory"]), f"<code>{esc(r['command'])}</code>", esc(r["exit_code"]), badge(r["result"]),
            esc(r["summary_line"]), esc(r["run_utc"]), link(r["source_url"], "verify.py"), esc(r["workflow_files"]) or "<span class=\"blank\">none</span>",
        ])
    ver_body = ("<p class=\"note\">Each verifier ran from the repository root in a scratch copy of the working tree, so a verifier that writes files cannot change the repo. "
                "The nba-commission verifier is included because it scans the whole repository; no CI workflow runs it. repo-review/verify.py reads this table, so it runs in its own workflow (repo-review.yml) rather than inside this sweep.</p>"
                + table(["Directory", "Command", "Exit", "Result", "Summary line", "Run (UTC)", "Source", "Workflows"],
                        ver_rows, "Verifier results"))
    (HERE / "verifiers.html").write_text(page("Verifiers", "verifiers.html", ver_body,
        "Result of every desk verify.py run from the repository root, with exit codes and the summary line each one printed."), encoding="utf-8")

    sc_rows = []
    for s in spots:
        sc_rows.append([
            esc(s["check_id"]), esc(s["area"]), link(s["official_url"], "official page"), esc(s["official_observation"]),
            esc(s["desk_value"]) + "<br>" + link(s["desk_url"], "desk file"), badge(s["result"]), esc(s["read_date"]), esc(s["notes"]),
        ])
    st_rows = []
    for r in standings:
        st_rows.append([
            esc(r["team"]), esc(r["official_wlt"]), esc(r["official_pf_pa"]),
            esc(r["desk_e1d60f5d_wlt"]) + " · " + esc(r["desk_e1d60f5d_pf_pa"]), badge(r["result_desk_e1d60f5d"]),
            esc(r["hub_official_wlt_dated_2026_11_13"]) + " · " + esc(r["hub_official_pf_pa"]), badge(r["result_hub"]),
            link(r["official_source_url"], "official"),
        ])
    sc_body = (table(["ID", "Check", "Official source", "What the official page shows", "Desk value", "Result", "Read", "Notes"], sc_rows, "Official spot-checks")
               + table(["Club", "Official W-L-T (18 Nov)", "Official PF/PA", "Desk capture 17 Nov: W-L-T · PF/PA", "Desk result", "Hub official (13 Nov): W-L-T · PF/PA", "Hub result", "Source"],
                       st_rows, "All 32 club records, line by line"))
    sc_body = ("<p class=\"note\">The official values were transcribed from the standings page and checked against the schedule page. "
               "League totals balance: 149 wins = 149 losses; 6,923 points for = 6,923 against.</p>" + sc_body)
    (HERE / "spot-checks.html").write_text(page("Official spot-checks", "spot-checks.html", sc_body,
        "Desk values compared with nfl.com on 18 Nov 2026: schedule, byes, Week 10 designations and all 32 team records."), encoding="utf-8")

    fl_rows = []
    for f in flags:
        fl_rows.append([
            f"<span id=\"{esc(f['flag_id'].lower())}\">{esc(f['flag_id'])}</span>", badge(f["severity"]), esc(f["area"]), esc(f["observation"]),
            link(f["evidence_url"], "evidence") + (f"<br><small>{esc(f['evidence_detail'])}</small>" if f["evidence_detail"] else ""),
            (link(f["official_url"], "official") if f["official_url"] else "<span class=\"blank\">n/a</span>"),
            badge(f["status"]), esc(f["action_needed"]),
        ])
    fl_body = ("<p class=\"note\">Flagged items are published for review and do not block the merge. Items marked FIXED were changed in this session; "
               "the evidence link shows the state after the fix.</p>"
               + table(["ID", "Severity", "Area", "Observation", "Evidence", "Official", "Status", "Action needed"], fl_rows, "Flagged for Review"))
    (HERE / "flagged.html").write_text(page("Flagged for Review", "flagged.html", fl_body,
        "Irregularities found in the repository review, each with its evidence link, status and the action needed."), encoding="utf-8")
    print(f"built inventory={len(inventory)} standings={len(standings)} spot={len(spots)} flags={len(flags)} verifiers={n_ver}")


if __name__ == "__main__":
    main()

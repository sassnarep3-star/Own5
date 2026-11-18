#!/usr/bin/env python3
"""Deterministic builder for the session 98a211b8 review desk (stdlib only).

Reads nfl-98a211b8/data/*.csv and nfl-98a211b8/captures/*, writes the static
HTML pages into nfl-98a211b8/. No timestamps are generated at build time, so
two builds of the same inputs are byte-identical.

Modes:
  python3 nfl-98a211b8/build.py                 render pages
  python3 nfl-98a211b8/build.py --check-rows    regenerate data/injury_row_checks.csv
  python3 nfl-98a211b8/build.py --scan          regenerate data/desk_index.csv
"""
import csv
import hashlib
import html
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(HERE, "data")
CAPTURES = os.path.join(HERE, "captures")
LIVE = "https://sassnarep3-star.github.io/Own5"
BLOB = "https://github.com/sassnarep3-star/Own5/blob/main/"
EXCERPT = "captures/nfl_reg10_chunk0_excerpt_2026-11-18.md"
REG10 = "https://www.nfl.com/injuries/league/2026/reg10"
REPO_COPY = "data/decision-desk/official/official_injuries_wk10.csv"
TEAMS = ("Commanders", "Giants", "Patriots", "Lions")

PAGES = [
    ("index.html", "Overview"),
    ("repo-review.html", "Repo review"),
    ("availability.html", "Official availability"),
    ("desks.html", "Desk index"),
    ("flagged.html", "Flagged for Review"),
    ("executive-summary.html", "Executive summary"),
    ("sources.html", "Sources"),
]


# ----------------------------------------------------------------- parsing
ROW_RE = re.compile(
    r"^\| \[(?P<player>[^\]]+)\]\((?P<url>https://www\.nfl\.com/players/[^)]+)\) \| "
    r"(?P<pos>[^|]*?) \| (?P<injury>[^|]*?) \| (?P<practice>[^|]*?) \| (?P<game>[^|]*?) \|\s*$"
)


def sha256_file(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def parse_official_rows(path):
    """Return official injury rows from the verbatim excerpt, with line numbers."""
    rows, team = [], None
    with open(path, encoding="utf-8") as fh:
        for no, raw in enumerate(fh, 1):
            s = raw.strip()
            if s in TEAMS:
                team = s
                continue
            m = ROW_RE.match(s)
            if m and team:
                rows.append({
                    "team_nickname": team,
                    "player": m.group("player"),
                    "position": m.group("pos").strip(),
                    "injury": m.group("injury").strip(),
                    "practice_status": m.group("practice").strip(),
                    "game_status": m.group("game").strip(),
                    "official_source_url": m.group("url"),
                    "official_line": no,
                })
    return rows


def load_repo_rows(path):
    """Return {(team_nickname, player): (row, line_no)} from the repo copy."""
    out = {}
    with open(path, encoding="utf-8", newline="") as fh:
        for no, row in enumerate(csv.DictReader(fh), 2):  # line 1 is the header
            out[(row["team_nickname"], row["player"])] = (row, no)
    return out


def compare_rows(official, repo_index, repo_path):
    """Field-by-field comparison. Returns one dict per official row."""
    result = []
    for o in official:
        key = (o["team_nickname"], o["player"])
        rec = {
            "team_nickname": o["team_nickname"],
            "player": o["player"],
            "official_position": o["position"],
            "official_injury": o["injury"],
            "official_practice_status": o["practice_status"],
            "official_game_status": o["game_status"],
            "official_line": o["official_line"],
            "official_source_url": REG10,
            "repo_source_path": repo_path,
        }
        if key not in repo_index:
            rec.update(repo_injury="", repo_practice_status="", repo_game_status="",
                       repo_line="", match="NOT IN REPO", differing_fields="player missing")
            result.append(rec)
            continue
        r, line = repo_index[key]
        diffs = []
        for field, rk, ok in (
            ("injury", r["injury"], o["injury"]),
            ("practice", r["practice_status"], o["practice_status"]),
            ("game", r["game_status"], o["game_status"]),
            ("position", r["position"], o["position"]),
        ):
            if rk.strip() != ok.strip():
                diffs.append(field)
        rec.update(repo_injury=r["injury"], repo_practice_status=r["practice_status"],
                   repo_game_status=r["game_status"], repo_line=line,
                   match="MATCH" if not diffs else "DIFFERS",
                   differing_fields=";".join(diffs))
        result.append(rec)
    return result


CHECK_COLS = ["team_nickname", "player", "official_position", "official_injury",
              "official_practice_status", "official_game_status", "repo_injury",
              "repo_practice_status", "repo_game_status", "match", "differing_fields",
              "official_line", "repo_line", "official_source_url", "repo_source_path"]


def write_row_checks():
    official = parse_official_rows(os.path.join(HERE, EXCERPT))
    repo_index = load_repo_rows(os.path.join(ROOT, REPO_COPY))
    rows = compare_rows(official, repo_index, REPO_COPY)
    out = os.path.join(DATA, "injury_row_checks.csv")
    with open(out, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CHECK_COLS, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in CHECK_COLS})
    return rows


def scan_desks():
    desks = []
    for name in sorted(os.listdir(ROOT)):
        path = os.path.join(ROOT, name)
        if not os.path.isdir(path) or name.startswith("."):
            continue
        if not (name.startswith("nfl") or name.startswith("own5")):
            continue
        idx = os.path.join(path, "index.html")
        has_index = os.path.isfile(idx)
        title = ""
        if has_index:
            with open(idx, encoding="utf-8", errors="replace") as fh:
                m = re.search(r"<title>(.*?)</title>", fh.read(), re.S | re.I)
                title = html.unescape(m.group(1)).strip() if m else ""
        n_files = sum(len(f) for _, _, f in os.walk(path))
        desks.append({
            "directory": name,
            "title": title,
            "has_index_html": "yes" if has_index else "no",
            "live_url": f"{LIVE}/{name}/" if has_index else "",
            "files": str(n_files),
            "github_link": f"https://github.com/sassnarep3-star/Own5/tree/main/{name}",
        })
    return desks


def write_desk_index():
    desks = scan_desks()
    cols = ["directory", "title", "has_index_html", "live_url", "files", "github_link"]
    with open(os.path.join(DATA, "desk_index.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        for d in desks:
            w.writerow(d)
    return desks


# ----------------------------------------------------------------- rendering
def read_table(name):
    with open(os.path.join(DATA, name), encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def e(text):
    return html.escape(str(text or ""), quote=True)


def link(url, label=None):
    if not url:
        return '<span class="badge warn">UNVERIFIED</span>'
    return f'<a href="{e(url)}" rel="noopener">{e(label or url)}</a>'


def badge(result):
    cls = {"PASS": "ok", "MATCH": "ok", "FLAG": "warn", "DIFFERS": "warn",
           "NOT IN REPO": "warn", "UNVERIFIED": "warn", "INFO": "info"}.get(result, "info")
    return f'<span class="badge {cls}">{e(result)}</span>'


def table(headers, rows_html):
    head = "".join(f"<th>{e(h)}</th>" for h in headers)
    body = "".join(f"<tr>{r}</tr>" for r in rows_html)
    return (f'<div class="tablewrap"><table><thead><tr>{head}</tr></thead>'
            f"<tbody>{body}</tbody></table></div>")


def td(content):
    return f"<td>{content}</td>"


def nav(active):
    items = []
    for fname, label in PAGES:
        cls = ' class="active"' if fname == active else ""
        items.append(f'<a href="{fname}"{cls}>{e(label)}</a>')
    return "<nav>" + "".join(items) + "</nav>"


def page(fname, title, body):
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)} · NFL review desk 98a211b8</title>
<style>
:root{{--ink:#1d2430;--mute:#5b6676;--line:#dfe4ec;--bg:#f7f9fc;--ok:#11703b;--warn:#9a5b00;--info:#1f4d8f}}
*{{box-sizing:border-box}}body{{margin:0;font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;color:var(--ink);background:var(--bg)}}
header{{background:#14213d;color:#fff;padding:18px 24px}}header h1{{margin:0;font-size:20px}}header p{{margin:4px 0 0;color:#c9d3e6;font-size:13px}}
nav{{display:flex;flex-wrap:wrap;gap:6px;padding:10px 24px;background:#fff;border-bottom:1px solid var(--line)}}
nav a{{padding:6px 10px;border-radius:6px;color:var(--info);text-decoration:none;font-weight:600}}nav a.active,nav a:hover{{background:#e8f0fb}}
main{{padding:20px 24px;max-width:1280px}}h2{{font-size:17px;margin:26px 0 8px}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px;margin:12px 0}}
.card{{background:#fff;border:1px solid var(--line);border-radius:10px;padding:12px 14px}}.card b{{display:block;font-size:22px}}.card span{{color:var(--mute);font-size:13px}}
.tablewrap{{overflow-x:auto;background:#fff;border:1px solid var(--line);border-radius:10px}}
table{{border-collapse:collapse;width:100%;font-size:13.5px}}th,td{{padding:7px 9px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}
th{{background:#f1f4f9;font-weight:600;position:sticky;top:0}}tr:last-child td{{border-bottom:0}}
.badge{{display:inline-block;padding:1px 7px;border-radius:999px;font-size:12px;font-weight:600;border:1px solid}}
.badge.ok{{color:var(--ok);border-color:#a8dcbc;background:#eefaf3}}.badge.warn{{color:var(--warn);border-color:#f0d39a;background:#fff8ea}}.badge.info{{color:var(--info);border-color:#bcd0ee;background:#eef4fc}}
p.note,.muted{{color:var(--mute);font-size:13.5px}}code{{font-size:12.5px;word-break:break-all}}a{{color:var(--info)}}
footer{{padding:18px 24px;color:var(--mute);font-size:12.5px}}
</style></head><body>
<header><h1>NFL review desk · session 98a211b8</h1>
<p>Repo review, dated official availability status, desk index, and a Flagged for Review register. Not a betting recommendation.</p></header>
{nav(fname)}
<main>{body}</main>
<footer>Generated by <code>nfl-98a211b8/build.py</code> from the CSVs in <code>nfl-98a211b8/data/</code>. Every row links its source, or is labelled UNVERIFIED. Public site: <a href="{LIVE}/">{LIVE}/</a></footer>
</body></html>
"""


def build_pages(out_dir):
    repo = read_table("repo_review.csv")
    caps = read_table("official_status_captures.csv")
    checks = read_table("injury_row_checks.csv")
    desks = read_table("desk_index.csv")
    unv = read_table("unverified.csv")
    sources = read_table("sources.csv")
    excerpt_sha = sha256_file(os.path.join(HERE, EXCERPT))

    n_pass = sum(1 for r in repo if r["result"] == "PASS")
    n_flag = sum(1 for r in repo if r["result"] == "FLAG")
    n_block = sum(1 for r in repo if r["result"] == "FLAG" and r["severity"] == "blocking")
    n_match = sum(1 for r in checks if r["match"] == "MATCH")
    n_diff = sum(1 for r in checks if r["match"] != "MATCH")
    n_desks = len(desks)
    n_index = sum(1 for d in desks if d["has_index_html"] == "yes")
    pinned = {c["excerpt_sha256"] for c in caps if c["excerpt_sha256"]}
    sha_ok = pinned == {excerpt_sha}

    pages = {}

    # ---- Overview
    cards = "".join(
        f'<div class="card"><b>{e(v)}</b><span>{e(k)}</span></div>' for k, v in [
            ("Repo review checks (PASS)", n_pass),
            ("Repo review checks (FLAG)", n_flag),
            ("Blocking flags", n_block),
            ("Official rows checked (WAS, NYG, NE, DET)", len(checks)),
            ("Rows matching the repo copy", n_match),
            ("Rows that differ from the repo copy", n_diff),
            ("NFL-related desk folders on main", n_desks),
            ("Desks with an index.html", n_index),
        ])
    links = "".join(
        f'<li><a href="{fn}">{e(lab)}</a></li>' for fn, lab in PAGES[1:])
    pages["index.html"] = ("Overview", f"""
<h2>Where things stand</h2>
<div class="cards">{cards}</div>
<p class="note">This page reports verified checks only. It does not publish a market line, an edge, a strategy result, or a bet. It is not a decision desk. The brief's other items (strategies, leaderboards, correlations, luck panel) are answered by the desks listed on <a href="desks.html">Desk index</a>; this session did not re-verify them.</p>
<h2>Sections</h2>
<ul>{links}</ul>
<h2>Most important finding</h2>
<p>The official Week 10 injury report (nfl.com, read before 2026-11-18T03:11:29Z) and the repo's copy (retrieved 2026-11-12T16:52:39Z) disagree on <b>{n_diff} of {len(checks)}</b> rows that were checked. Three Lions players listed Out on the official page (Kerby Joseph, Cade Mays, D.J. Reed) have blank game-status cells in the repo copy. The Week 11 report is not served at read time, so no Week 11 availability value is published. See <a href="availability.html">Official availability</a>.</p>
""")

    # ---- Repo review
    rr = []
    for r in repo:
        rr.append("".join([
            td(e(r["id"])), td(e(r["area"])), td(e(r["check"])), td(e(r["observed"])),
            td(e(r["reference"])), td(badge(r["result"])), td(e(r["severity"])),
            td(link(r["evidence_link"], "repo evidence")),
            td(link(r["official_source_link"], "official link") if r["official_source_link"].startswith("https://www.nfl.com") or r["official_source_link"].startswith("https://api.github.com") else '<span class="muted">INTERNAL (repo fact)</span>'),
            td(e(r["verified_utc"])), td(e(r["note"])),
        ]))
    pages["repo-review.html"] = ("Repo review", f"""
<h2>Repo review register</h2>
<p class="note">Each row is one check against the committed files or an official page. Repo-only facts are labelled INTERNAL and have a link to the file or run. Read-only: no file in another session's namespace was changed.</p>
{table(["ID","Area","Check","Observed","Reference","Result","Severity","Evidence","Official source","Verified (UTC)","Note"], rr)}
""")

    # ---- Availability
    cap_rows = []
    for c in caps:
        cap_rows.append("".join([
            td(e(c["capture_id"])),
            td(link(c["requested_url"]) if c["requested_url"].startswith("https") else e(c["requested_url"]) + ' <span class="muted">(INTERNAL repo file)</span>'),
            td(link(c["resolved_url"]) if c["resolved_url"].startswith("https") else '<span class="muted">n/a</span>'),
            td(e(c["title_returned"])), td(e(c["method"])), td(e(c["acquired_utc"])),
            td(f'{e(c["chunks_read"])} of {e(c["chunks_total"])}' if c["chunks_total"] else "n/a"),
            td(f'<code>{e(c["excerpt_file"])}</code><br><span class="muted">sha256 {excerpt_sha}</span>' if c["excerpt_file"] and c["capture_id"] in ("C01", "C02") else (f'<code>{e(c["excerpt_file"])}</code>' if c["excerpt_file"] else '<span class="muted">none</span>')),
            td(e(c["result"])), td(e(c["note"])),
        ]))
    ch_rows = []
    for r in checks:
        ch_rows.append("".join([
            td(e(r["team_nickname"])), td(e(r["player"])),
            td(e(r["official_injury"])), td(e(r["official_practice_status"])), td(e(r["official_game_status"])),
            td(e(r["repo_injury"])), td(e(r["repo_practice_status"])), td(e(r["repo_game_status"])),
            td(badge(r["match"])), td(e(r["differing_fields"])),
            td(link(r["official_source_url"], "nfl.com (Week 10)")),
            td(f'<span class="muted">excerpt line {e(r["official_line"])} · repo line {e(r["repo_line"])}</span>'),
        ]))
    unv_rows = [
        "".join([td(e(u["id"])), td(e(u["item"])), td(badge(u["status"])), td(e(u["why_unverified"])),
                 td(link(u["official_source_link"]) if u["official_source_link"] else '<span class="badge warn">UNVERIFIED</span>')])
        for u in unv]
    pages["availability.html"] = ("Official availability", f"""
<h2>Capture log (official pages read this session)</h2>
<p class="note">Each official read records the URL requested, the URL resolved, the title returned, the time before which it was acquired, how much was read, and the SHA-256 of the saved excerpt. Only chunk 0 of the Week 10 report was read, so this is not a full capture.</p>
{table(["Capture","Requested","Resolved","Title returned","Method","Acquired (UTC)","Read","Saved excerpt","Result","Note"], cap_rows)}
<h2>Line-by-line: 44 visible official rows against the repo copy</h2>
<p class="note">Official values are from the verbatim excerpt (<code>{e(EXCERPT)}</code>). Repo values are from <code>{e(REPO_COPY)}</code>, retrieved 2026-11-12T16:52:39Z. A difference may be a later official revision or a parse defect; one read cannot separate them.</p>
{table(["Club","Player","Official injury","Official practice","Official game status","Repo injury","Repo practice","Repo game status","Match","Differing fields","Official source","Lines"], ch_rows)}
<h2>Not verified in this session</h2>
{table(["ID","Item","Status","Why","Official source"], unv_rows)}
""")

    # ---- Desk index
    d_rows = []
    for d in desks:
        d_rows.append("".join([
            td(f'<code>{e(d["directory"])}</code>'),
            td(e(d["title"]) or '<span class="muted">no index.html</span>'),
            td(badge("PASS" if d["has_index_html"] == "yes" else "UNVERIFIED")),
            td(link(d["live_url"], "live page") if d["live_url"] else '<span class="muted">none</span>'),
            td(e(d["files"])),
            td(link(d["github_link"], "repo folder")),
        ]))
    pages["desks.html"] = ("Desk index", f"""
<h2>NFL-related desks on main</h2>
<p class="note">Generated by <code>build.py --scan</code> from the folders in the checkout. The index does not rank the desks and does not say which is current. The root index.html links only one of them (repo-review R02). Its build date is not shown here because a git-derived date would differ between a CI clone and a full clone.</p>
{table(["Folder","Title","index.html","Live page","Files","Repo"], d_rows)}
""")

    # ---- Flagged
    fl = [r for r in repo if r["result"] == "FLAG"]
    fl_rows = ["".join([
        td(e(r["id"])), td(e(r["area"])), td(e(r["check"])), td(badge(r["result"])), td(e(r["severity"])),
        td(e(r["observed"])), td(link(r["evidence_link"], "evidence")),
        td(link(r["official_source_link"], "official") if r["official_source_link"].startswith("https://www.nfl.com") else '<span class="muted">INTERNAL</span>'),
        td(e(r["note"])),
    ]) for r in fl]
    unv_flag = ["".join([
        td(e(u["id"])), td(e(u["item"])), td(badge(u["status"])), td(e(u["why_unverified"])),
        td(link(u["official_source_link"]) if u["official_source_link"] else '<span class="badge warn">UNVERIFIED</span>'),
    ]) for u in unv]
    pages["flagged.html"] = ("Flagged for Review", f"""
<h2>Flagged for Review</h2>
<p class="note">Nothing on this page blocks a merge. Each item has a link for manual review. Requests to other sessions are logged on COORDINATION.md and are not actioned here.</p>
<h2>Irregularities (repo review FLAG rows)</h2>
{table(["ID","Area","Check","Result","Severity","Observed","Evidence","Official","Note"], fl_rows)}
<h2>Unverified items (left blank, not inferred)</h2>
{table(["ID","Item","Status","Why unverified","Official source"], unv_flag)}
<h2>Requests logged for other sessions (not actioned)</h2>
<ul>
<li>Integration session: root <code>index.html</code> should list every NFL desk with its capture date (R02).</li>
<li>Owners of the results feed (e46fb855, ce1f16ff): apply the alias map <code>{{LAR:LA, ARI:AZ}}</code> and reconcile club by club before any team-level join (R09). Desk 35a1feb2 gives the full map.</li>
<li>Owners of the injury captures: capture the official report on each publication day with a fetch time and keep the raw hash. A single read cannot settle the 17 differences (R13).</li>
<li>Owners of the injury CSVs: point each row's source link at the week's page (R16).</li>
<li>Integration session: separate the workflow file name from its content (R04), fix the README table split (R05), and close or refresh the nine open PRs (R08).</li>
</ul>
""")

    # ---- Executive summary
    pages["executive-summary.html"] = ("Executive summary", f"""
<h2>What this session did</h2>
<ul>
<li>Reviewed the repo's shared board, live site, workflows and open PRs, and recorded {len(repo)} checks ({n_pass} PASS, {n_flag} FLAG).</li>
<li>Read the official Week 10 injury report from nfl.com (chunk 0 of 8, 44 rows across four clubs) and compared each row with the repo's copy: <b>{n_match} match, {n_diff} differ</b>.</li>
<li>Requested the official Week 11 injury page: at read time the request resolved to the Week 10 URL, so the Week 11 report was not served. No Week 11 availability is published here.</li>
<li>Built a desk index of {n_desks} NFL-related folders and this Flagged for Review register.</li>
</ul>
<h2>Verified findings (each with a link)</h2>
<ul>
<li>Lions: Kerby Joseph, Cade Mays and D.J. Reed are <b>Out</b> on the official page. The repo copy has blank game status for all three (<a href="availability.html">rows</a>; <a href="{REG10}">official page</a>).</li>
<li>Results feed: 18 club-game appearances use <code>ARI</code>/<code>LAR</code>, while the official standings use <code>AZ</code>/<code>LA</code> (<a href="repo-review.html">R09</a>). A team-level join on code would silently lose them.</li>
<li>Completed games: the feed has 145 FINAL rows (read 2026-11-15), the 2026-11-17 standings imply 149. The feed is stale, not wrong (<a href="repo-review.html">R10</a>).</li>
<li>Market prices: the statement that none exist in the repo is false. A third-party log has spread, total and moneyline for 163 of 272 games. The question of whether third-party prices may be used is still open (<a href="repo-review.html">R11</a>).</li>
<li>Week 10 report: the official row count was not settled. The repo has 276 rows, and other desks record 254 and 279 (<a href="repo-review.html">R14</a>).</li>
</ul>
<h2>What is still unknown</h2>
<ul>
<li>Week 11 availability for any club (report not yet served at read time).</li>
<li>Whether the 17 differing rows are later official revisions or parse errors. A dated daily capture from Wednesday onward is the test.</li>
<li>Whether any Houston depth value is usable (image-only publication).</li>
</ul>
<h2>Decisions needed from you</h2>
<ol>
<li><b>Canonical desk.</b> {n_desks - 1} other NFL-related folders answer the same brief. Choose one to keep as the entry point, and say which others to archive.</li>
<li><b>Price-source policy.</b> Decide whether third-party prices (for example the nflverse-derived log) may be used for origination, or whether only official prices qualify. Until decided, prices stay blank.</li>
<li><b>Capture schedule.</b> Approve a daily official capture from Wednesday to kickoff with stored hashes, so the 17 differences can be explained.</li>
</ol>
<p class="note">No strategy, edge, return, correlation or leaderboard value is claimed here. Those belong to the other desks and are not re-verified in this session.</p>
""")

    # ---- Sources
    s_rows = ["".join([
        td(e(s["source_id"])), td(e(s["publisher"])), td(link(s["url"])),
        td(e(s["used_for"])), td(e(s["access_utc"])), td(e(s["access_method"])), td(e(s["class"])),
    ]) for s in sources]
    pages["sources.html"] = ("Sources", f"""
<h2>Sources used in this session</h2>
<p class="note">Class: <b>official</b> = nfl.com; <b>repository</b> = a GitHub-hosted fact about this repo; <b>third-party</b> = not an official source, named only for provenance.</p>
{table(["ID","Publisher","URL","Used for","Accessed (UTC)","Method","Class"], s_rows)}
""")

    os.makedirs(out_dir, exist_ok=True)
    for fname, (title, body) in pages.items():
        with open(os.path.join(out_dir, fname), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(page(fname, title, body))
    return sorted(pages)


def main(argv):
    if "--check-rows" in argv:
        rows = write_row_checks()
        print(f"injury_row_checks.csv: {len(rows)} rows, "
              f"{sum(1 for r in rows if r['match'] == 'MATCH')} match")
    if "--scan" in argv:
        desks = write_desk_index()
        print(f"desk_index.csv: {len(desks)} folders")
    if "--no-render" not in argv:
        names = build_pages(HERE)
        print("rendered:", ", ".join(names))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

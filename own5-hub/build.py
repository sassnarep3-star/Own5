#!/usr/bin/env python3
"""Render the Own5 hub (static HTML) from own5-hub/data/*.csv and own5-hub/captures/*.csv (stdlib only).

Every table row is generated from a data row. A row either carries a link to the source it cites,
or it shows an UNVERIFIED / NO SOURCE badge. verify.py enforces this on the rendered HTML.
"""
import csv, datetime as dt, glob, html, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "data")
C = os.path.join(HERE, "captures")
BUILT_UTC = "2026-11-18"


def read(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def esc(s):
    return html.escape(s or "", quote=True)


def link(url, label=None):
    if not url:
        return '<span class="badge warn">NO SOURCE</span>'
    return f'<a href="{esc(url)}" rel="noopener">{esc(label or url)}</a>'


def status_badge(s):
    cls = {"DONE": "ok", "RESOLVED": "ok", "MATCH": "ok", "CONFIRMED": "ok", "MATCH (resolved)": "ok",
           "PARTIAL": "mid", "STARTED-TODAY": "mid", "RULE-ONLY": "mid", "BLOCKED": "bad",
           "NOT-MET": "bad", "CONTRADICTED": "bad", "DECISION": "bad", "REJECTED": "muted",
           "NOT ESTABLISHED": "warn", "MISMATCH": "bad", "CONSISTENT": "mid"}
    key = next((k for k in cls if s.upper().startswith(k.upper())), None)
    return f'<span class="badge {cls.get(key, "muted")}">{esc(s)}</span>'


def page(title, active, body, sub=""):
    nav = [("index.html", "Dashboard"), ("executive-summary.html", "Executive summary"),
           ("requirements.html", "Requirements"), ("verified.html", "Verified today"),
           ("injuries.html", "Injury captures"), ("questions.html", "Questions"),
           ("suggestions.html", "Suggestions"), ("flagged.html", "Flagged for Review"),
           ("sources.html", "Sources")]
    links = "".join(f'<a href="{h}"{" class=active" if h == active else ""}>{t}</a>' for h, t in nav)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · Own5 NFL hub</title>
<link rel="stylesheet" href="assets/hub.css">
</head><body>
<header class="top"><div class="brand">Own5 · NFL line-origination hub</div><nav>{links}</nav></header>
<main>
<h1>{esc(title)}</h1>
{f'<p class="sub">{esc(sub)}</p>' if sub else ''}
{body}
</main>
<footer>Built {BUILT_UTC} from data files in <code>own5-hub/data/</code> and <code>own5-hub/captures/</code>.
Official sources are linked on every row. Anything without a source is badged and listed on
<a href="flagged.html">Flagged for Review</a>. Nothing here is a betting recommendation.</footer>
</body></html>
"""


def table(headers, rows_html):
    head = "".join(f"<th>{esc(h)}</th>" for h in headers)
    return f'<div class="tw"><table><thead><tr>{head}</tr></thead><tbody>{"".join(rows_html)}</tbody></table></div>'


def cell(x, raw=False):
    return f"<td>{x if raw else esc(x)}</td>"


def build():
    req = read(os.path.join(D, "requirements.csv"))
    checks = read(os.path.join(D, "verified_checks.csv"))
    qs = read(os.path.join(D, "questions.csv"))
    sug = read(os.path.join(D, "suggestions.csv"))
    flags = read(os.path.join(D, "flagged.csv"))
    srcs = read(os.path.join(D, "sources.csv"))
    manifest = read(os.path.join(C, "manifest.csv")) if os.path.exists(os.path.join(C, "manifest.csv")) else []
    counts = read(os.path.join(C, "injury_counts_daily.csv")) if os.path.exists(os.path.join(C, "injury_counts_daily.csv")) else []
    out = {}

    from collections import Counter
    st = Counter(r["status"] for r in req)
    open_flags = [f for f in flags if not f["status"].lower().startswith(("resolved",))]
    ok_checks = sum(1 for c in checks if c["result"].upper().startswith(("MATCH", "CONFIRMED", "CONSISTENT")))
    bad_checks = sum(1 for c in checks if c["result"].upper().startswith(("MISMATCH", "CONTRADICTED", "NOT ESTABLISHED")))

    def stat(n, label, cls=""):
        return f'<div class="card {cls}"><div class="n">{n}</div><div class="l">{esc(label)}</div></div>'

    cards = "".join([
        stat(len(req), "requirements tracked"),
        stat(st.get("DONE", 0) + st.get("RESOLVED", 0), "done in the repo (repo claims unless re-checked)", "ok"),
        stat(st.get("PARTIAL", 0) + st.get("STARTED-TODAY", 0), "partial or started today", "mid"),
        stat(st.get("BLOCKED", 0) + st.get("NOT-MET", 0) + st.get("DECISION", 0), "blocked, decision or not met", "bad"),
        stat(ok_checks, "official re-checks that match", "ok"),
        stat(bad_checks, "re-checks that contradict or are unresolved", "bad"),
        stat(len(open_flags), "open items on Flagged for Review", "warn"),
        stat(len(manifest), "official captures in the ledger"),
    ])

    rr = []
    for r in req:
        rr.append("<tr>" + cell(r["id"]) + cell(r["requirement"]) + cell(status_badge(r["status"]), True)
                  + cell(r["blocking_gate"]) + cell(r["number_that_clears_it"] if "number_that_clears_it" in r else r["number_that_clears"])
                  + cell(link(r["source_url"], r["source_class"] + " ↗") if r["source_url"] else ("<span class=\"badge muted\">" + esc(r["source_class"]) + "</span> " + '<span class="badge warn">NO SOURCE</span>'), True)
                  + cell(r["verification"]) + "</tr>")
    readiness = table(["ID", "Requirement", "Status", "Gate that blocks it", "Number that clears it", "Source", "Verification"], rr)

    idx = f"""
<div class="cards">{cards}</div>
<section class="callout">
<strong>Start here.</strong> Official data was re-read on 2026-11-18 and the daily capture of the official injury report has started.
Three things changed the picture: (1) GitHub runners can reach the official NFL pages, so the "unreachable" blocker applies only to this sandbox;
(2) the brief's Week 10 counts (254 and 279 rows, 6 designations) are contradicted by today's official report (347 rows, 171 designations);
(3) the three Lions designations are now Out on the official page. Read <a href="executive-summary.html">the executive summary</a>,
then <a href="flagged.html">Flagged for Review</a>.
</section>
<h2>Decision readiness: one row per requirement</h2>
<p class="sub">Each row names the status, the gate that blocks it, and the number that would clear it. Status words come from the repo or the re-check named in the verification column.</p>
{readiness}
"""
    out["index.html"] = page("Decision dashboard", "index.html", idx, "What is done, what is blocked, and what would clear each item.")

    es = f"""
<section class="prose">
<h2>What is true today</h2>
<ul>
<li><strong>Official injury report (captured 2026-11-18T03:28:38Z):</strong> 28 club tables, 347 player rows, 171 rows with a game status (Out 70, Questionable 90, Doubtful 11). Source: <a href="https://www.nfl.com/injuries/">nfl.com/injuries</a>. See <a href="injuries.html">injury captures</a>.</li>
<li><strong>Lions:</strong> Kerby Joseph, Cade Mays and D.J. Reed are Out on the official page (resolves a long-standing blank). <a href="https://www.nfl.com/injuries/">Source</a>.</li>
<li><strong>Malik Willis</strong> is listed as Reserve/Injured (MIA, 11/10) on the official November reserve list, which is why he is absent from the report. <a href="https://www.nfl.com/transactions/league/reserve-list/2026/11">Source</a>.</li>
<li><strong>Standings:</strong> 30 of 32 clubs match the repo's stored standings exactly. BAL and LAC are one game further on at the official page. The repo's totals are stale by that game. <a href="https://www.nfl.com/standings/league/2026/REG">Source</a>.</li>
<li><strong>Luck panel:</strong> recomputed from the repo's standings with a 2.37 exponent convention, 0 mismatches; spread 4.34 wins (DEN +2.17, TB -2.17). It bounds luck; it does not remove it.</li>
<li><strong>Automation:</strong> a GitHub-hosted runner received HTTP 200 for the three official pages. A daily capture now writes hashes, UTC timestamps and structural pins.</li>
</ul>
<h2>What is blocked, and by what</h2>
<ul>
<li><strong>Prices.</strong> No admitted operator price. The price-data policy (decision D1) is open, so no CLV, residual or backtest ROI can be published as verified.</li>
<li><strong>Depth and snaps.</strong> No verified depth-order source for 32 clubs and no admitted snap-count or game-book source. The Texans depth chart is an image.</li>
<li><strong>Reserve completeness.</strong> The November list shows 25 rows. A cap is not established, so "not listed" still cannot be read as "available" for every club.</li>
<li><strong>History.</strong> One official season in the repo. Holdout and ablation studies need at least three.</li>
<li><strong>Storage terms.</strong> The raw captures sit in a public repository. The nfl.com terms page was not found at the URL tried.</li>
</ul>
<h2>What we recommend, and what needs your choice</h2>
<p>Nothing has been implemented from the suggestions. Each one is listed with its options and what would change our mind on the <a href="suggestions.html">suggestions page</a>.
The three most consequential are S03 (price-data policy), S04 (where raw captures live) and S05 (depth route).</p>
<h2>Repo review</h2>
<p>Irregularities in other desks are listed on <a href="flagged.html">Flagged for Review</a> with links. The largest: 24 requirement rows in one desk cite a page that cannot support them (F07); other desks still publish the stale 254 and 279 counts (F02). Corrections are requested, not made, in those desks.</p>
</section>
"""
    out["executive-summary.html"] = page("Executive summary", "executive-summary.html", es, "Short, sourced, and dated 2026-11-18.")

    rq = []
    for r in req:
        rq.append("<tr>" + cell(r["id"]) + cell(r["requirement"]) + cell(status_badge(r["status"]), True)
                  + cell(r["evidence_in_repo"]) + cell(r["source_class"])
                  + cell(link(r["source_url"], "source ↗") if r["source_url"] else '<span class="badge warn">NO SOURCE</span>', True)
                  + cell(r["blocking_gate"]) + cell(r["number_that_clears"]) + cell(r["verification"]) + "</tr>")
    out["requirements.html"] = page("Requirements register", "requirements.html", table(
        ["ID", "Requirement (from the brief)", "Status", "Evidence in repo", "Source class", "Source", "Blocking gate", "Number that clears it", "Verification"], rq),
        "All 80 lines grouped from the brief. Status is the repo's, unless the verification column says it was re-checked on 2026-11-18.")

    vc = []
    for c in checks:
        vc.append("<tr>" + cell(c["id"]) + cell(c["check"]) + cell(c["official_value_read"]) + cell(c["repo_or_brief_value"])
                  + cell(status_badge(c["result"]), True) + cell(link(c["source_url"], "official ↗" if "nfl.com" in c["source_url"] else "source ↗") if c["source_url"] else '<span class="badge warn">NO SOURCE</span>', True)
                  + cell(c["how_checked"]) + "</tr>")
    out["verified.html"] = page("Verified today", "verified.html", table(
        ["ID", "Check", "Official value (read 2026-11-18)", "Repo or brief value", "Result", "Source", "How checked"], vc),
        "Each row is a re-check made in this session against the official page, the runner capture, or the repo file it names.")

    # injuries: derived counts (per club), conflict flags between captures, deltas, and the capture ledger
    content = read(os.path.join(C, "parsed_content_daily.csv")) if os.path.exists(os.path.join(C, "parsed_content_daily.csv")) else []
    flags_rows = []
    for a, b in zip(content, content[1:]):
        raw_changed = a["raw_sha256"] != b["raw_sha256"]
        parsed_changed = a["parsed_rows_sha256"] != b["parsed_rows_sha256"]
        if parsed_changed:
            verdict = "PARSED ROWS CHANGED: delta below"
        elif raw_changed:
            verdict = "raw bytes changed, parsed rows identical (non-substantive)"
        else:
            verdict = "no change"
        flags_rows.append("<tr>" + cell(a["capture_stamp_utc"] + " → " + b["capture_stamp_utc"]) + cell(str(raw_changed).lower())
                          + cell(str(parsed_changed).lower()) + cell(verdict)
                          + cell(link("https://www.nfl.com/injuries/", "official report ↗"), True) + "</tr>")
    conflict_html = ("<h2>Conflict flags between captures</h2>"
                     "<p class=\"sub\">A raw-hash alarm alone over-flags: the page carries a random id. The parsed-row hash decides.</p>"
                     + (table(["Pair", "Raw bytes changed", "Parsed rows changed", "Verdict", "Source"], flags_rows) if flags_rows
                        else "<p>Needs two captures to compare.</p>"))
    stamps = sorted({r["capture_stamp_utc"] for r in counts})
    latest = stamps[-1] if stamps else None
    club_rows = []
    if latest:
        for r in [x for x in counts if x["capture_stamp_utc"] == latest]:
            club_rows.append("<tr>" + cell(r["club"]) + cell(r["player_rows"]) + cell(r["rows_with_injury_label"])
                             + cell(r["game_status_out"]) + cell(r["game_status_questionable"]) + cell(r["game_status_doubtful"])
                             + cell(link("https://www.nfl.com/injuries/", "official report ↗"), True) + "</tr>")
    delta_html = ""
    if len(stamps) >= 2:
        prev, last = stamps[-2], stamps[-1]
        pc = {r["club"]: r for r in counts if r["capture_stamp_utc"] == prev}
        lc = {r["club"]: r for r in counts if r["capture_stamp_utc"] == last}
        drows = []
        for club in sorted(set(pc) | set(lc)):
            a_, b_ = pc.get(club), lc.get(club)
            if not a_ or not b_:
                drows.append("<tr>" + cell(club) + cell("club present in one capture only") + cell("") + cell("") + cell(link("https://www.nfl.com/injuries/", "official report ↗"), True) + "</tr>")
                continue
            d = {k: int(b_[k]) - int(a_[k]) for k in ["player_rows", "game_status_out", "game_status_questionable", "game_status_doubtful"]}
            if any(d.values()):
                drows.append("<tr>" + cell(club) + cell(f"{d['player_rows']:+d}") + cell(f"Out {d['game_status_out']:+d}, Questionable {d['game_status_questionable']:+d}, Doubtful {d['game_status_doubtful']:+d}") + cell(f"{prev} → {last}") + cell(link("https://www.nfl.com/injuries/", "official report ↗"), True) + "</tr>")
        delta_html = ("<h2>Delta since the previous capture (changes only)</h2>"
                      + (table(["Club", "Player rows change", "Designation change", "Captures", "Source"], drows) if drows else "<p>No club changed between the two captures.</p>"))
    delta_note = (f"<p class=\"sub\">Captures so far: {len(stamps)}. The delta table below appears when two captures differ in parsed content.</p>")
    man_rows = []
    for m in manifest:
        man_rows.append("<tr>" + cell(m["captured_utc"]) + cell(m["name"]) + cell(m["http_status"]) + cell(m["bytes"])
                        + cell(m["sha256_raw"][:16] + "…" if m["sha256_raw"] else "") + cell(m["pins_passed"])
                        + cell(link(m["url"], "source ↗"), True) + "</tr>")
    inj = (delta_note + delta_html + conflict_html
           + f"<h2>Club counts from the latest capture ({esc(latest or 'none')})</h2>"
           + (table(["Club", "Player rows", "Rows with an injury label", "Game status Out", "Questionable", "Doubtful", "Source"], club_rows) if club_rows else "<p>No parsed capture yet.</p>")
           + "<h2>Capture ledger</h2><p class=\"sub\">Hashes are sha256 of the raw bytes. Raw injury HTML is stored gzipped in the repo; standings and reserve pages keep hash and size only.</p>"
           + table(["Captured (UTC)", "Source", "HTTP", "Bytes", "sha256 (first 16)", "Pins passed", "Source"], man_rows))
    out["injuries.html"] = page("Injury report captures", "injuries.html", inj,
                                "Daily official captures with clock time and hash. Counts only, no player names on this page.")

    qr = []
    for q in qs:
        qr.append("<tr>" + cell(q["id"]) + cell(q["question"]) + cell(q["known_now"]) + cell(q["missing"])
                  + cell(q["cheapest_route_to_answer"]) + cell(q["blocks"]) + "</tr>")
    out["questions.html"] = page("Questions and information gaps", "questions.html", table(
        ["ID", "Question", "Known now", "Missing", "Cheapest route to an answer", "Blocks"], qr),
        "What must be answered before any decision can be made on the information we have.")

    sr = []
    for s in sug:
        sr.append("<tr>" + cell(s["id"]) + cell(s["suggestion"]) + cell(s["options"]) + cell(s["recommendation"])
                  + cell(s["what_would_change_our_mind"]) + cell(status_badge(s["status"].upper() if False else "DECISION" if "awaiting" in s["status"] else s["status"]), True) + "</tr>")
    out["suggestions.html"] = page("Suggestions (review before anything changes)", "suggestions.html", table(
        ["ID", "Suggestion", "Options", "Recommendation", "What would change our mind", "Status"], sr),
        "Nothing on this page has been implemented. Pick an option per row; the implementation follows your choice.")

    fr = []
    for f in flags:
        fr.append("<tr>" + cell(f["id"]) + cell(f["type"]) + cell(f["item"]) + cell(f["evidence"])
                  + cell(link(f["source_url"], "source ↗") if f["source_url"] else '<span class="badge warn">UNVERIFIED</span>', True)
                  + cell(f["status"]) + "</tr>")
    out["flagged.html"] = page("Flagged for Review", "flagged.html", table(
        ["ID", "Type", "Item", "Evidence", "Source", "Status"], fr),
        "Irregularities and unverified items. They do not block publication. Each row links to the source to check.")

    sc = []
    for s in srcs:
        sc.append("<tr>" + cell(s["id"]) + cell(s["source"]) + cell(link(s["url"]), True) + cell(s["what_it_supports"])
                  + cell(s["read_how"]) + cell(s["read_date"]) + "</tr>")
    out["sources.html"] = page("Sources", "sources.html", table(
        ["ID", "Source", "URL", "What it supports", "How it was read", "Read date"], sc),
        "Every source used in this hub, with how it was read.")

    for name, body in out.items():
        with open(os.path.join(HERE, name), "w", encoding="utf-8") as f:
            f.write(body)
    os.makedirs(os.path.join(HERE, "assets"), exist_ok=True)
    with open(os.path.join(HERE, "assets", "hub.css"), "w", encoding="utf-8") as f:
        f.write(CSS)
    return sorted(out)


CSS = """
:root{--ink:#1d2430;--mut:#667085;--line:#e4e7ec;--bg:#f7f8fa;--ok:#067647;--okbg:#ecfdf3;--mid:#7a4f00;--midbg:#fffaeb;--bad:#b42318;--badbg:#fef3f2;--warn:#8a4b00;--warnbg:#fff4e5;--muted:#475467;--mutedbg:#f2f4f7;--acc:#1849a9}
*{box-sizing:border-box}body{margin:0;font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;color:var(--ink);background:var(--bg)}
header.top{background:#fff;border-bottom:1px solid var(--line);padding:10px 20px;position:sticky;top:0;z-index:2}
.brand{font-weight:700;margin-bottom:6px}nav{display:flex;flex-wrap:wrap;gap:4px 14px}nav a{color:var(--acc);text-decoration:none;font-size:14px}nav a.active{font-weight:700;text-decoration:underline}
main{max-width:1280px;margin:0 auto;padding:18px 20px 40px}h1{font-size:26px;margin:8px 0 4px}h2{font-size:19px;margin:26px 0 8px}
.sub{color:var(--mut);margin:0 0 14px}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin:8px 0 16px}
.card{background:#fff;border:1px solid var(--line);border-radius:10px;padding:12px}.card .n{font-size:26px;font-weight:700}.card .l{color:var(--mut);font-size:13px}
.card.ok{border-left:4px solid var(--ok)}.card.mid{border-left:4px solid #b54708}.card.bad{border-left:4px solid var(--bad)}.card.warn{border-left:4px solid #dc6803}
.callout{background:#fff;border:1px solid var(--line);border-left:4px solid var(--acc);border-radius:10px;padding:12px 14px}
.tw{overflow:auto;background:#fff;border:1px solid var(--line);border-radius:10px}table{border-collapse:collapse;width:100%;font-size:13.5px}
th,td{text-align:left;vertical-align:top;padding:8px 10px;border-bottom:1px solid var(--line)}th{background:#f9fafb;position:sticky;top:0;font-size:12.5px;color:var(--muted)}
tr:last-child td{border-bottom:0}td a{color:var(--acc)}
.badge{display:inline-block;padding:1px 8px;border-radius:999px;font-size:12px;font-weight:600;white-space:nowrap}
.badge.ok{background:var(--okbg);color:var(--ok)}.badge.mid{background:var(--midbg);color:var(--mid)}.badge.bad{background:var(--badbg);color:var(--bad)}
.badge.warn{background:var(--warnbg);color:var(--warn)}.badge.muted{background:var(--mutedbg);color:var(--muted)}
.prose{background:#fff;border:1px solid var(--line);border-radius:10px;padding:6px 18px 14px}.prose li{margin:4px 0}.prose a{color:var(--acc)}
footer{max-width:1280px;margin:0 auto;padding:0 20px 30px;color:var(--mut);font-size:12.5px}code{font-size:12.5px}
"""

if __name__ == "__main__":
    print("pages:", ", ".join(build()))

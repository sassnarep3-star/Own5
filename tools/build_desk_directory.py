#!/usr/bin/env python3
"""Build the NFL desk directory (nfl-desk-5c5f4aaf/index.html + data/desks.csv).

Scope and honesty rules
- The directory is an index of REPOSITORY ARTEFACTS (desk folders, their entry pages and
  their flagged-item files). It makes no claim about the NFL, so it has no official-source column.
  Every number on it is counted from files on disk at build time.
- Nothing is read from git history, the clock, or the network, so two builds from the same tree
  are byte-identical (the same reason the root build is checked for determinism).
- Each desk's title comes from its own <title> tag, not from a hand-typed list.

Usage:
  python3 tools/build_desk_directory.py          # write the page and the CSV
  python3 tools/build_desk_directory.py --check  # build twice, require identical bytes and
                                                 # require every link on the page to resolve
"""
from __future__ import annotations

import csv
import html
import io
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "nfl-desk-5c5f4aaf"
OUT_HTML = OUT_DIR / "index.html"
OUT_CSV = OUT_DIR / "data" / "desks.csv"

# A directory is an NFL desk if its name says so. The two exceptions are the pre-existing
# Own5 desk and the NFL model folder, which carry NFL work under other names.
EXTRA_DESKS = {"own5-desk", "nfl_model"}
SKIP_DIRS = {".git", ".github", "tools", "tests", "scripts", "site", "research", "docs", "assets", "pages",
             "analysis", "artifacts", "data", "nfl-desk-5c5f4aaf"}


def is_nfl_desk(name: str) -> bool:
    return (name.startswith("nfl") or name in EXTRA_DESKS) and name not in SKIP_DIRS


def title_of(index: Path) -> str:
    try:
        text = index.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    m = re.search(r"<title>(.*?)</title>", text, re.S | re.I)
    return html.unescape(m.group(1)).strip() if m else ""


def flagged_files(desk: Path) -> list[Path]:
    found = []
    for p in sorted(desk.rglob("*")):
        if p.is_file() and p.name.lower().startswith("flagged.") and ".git" not in p.parts:
            found.append(p)
    return found


def csv_data_rows(path: Path) -> int | None:
    if path.suffix.lower() != ".csv":
        return None
    with path.open(encoding="utf-8", errors="replace", newline="") as fh:
        rows = list(csv.reader(fh))
    # Header row is excluded; blank lines are excluded.
    return sum(1 for r in rows[1:] if any(c.strip() for c in r))


def file_count(desk: Path) -> int:
    return sum(1 for p in desk.rglob("*") if p.is_file() and ".git" not in p.parts)


def collect() -> list[dict]:
    rows = []
    for d in sorted(ROOT.iterdir(), key=lambda p: p.name):
        if not d.is_dir() or not is_nfl_desk(d.name) or d.name.startswith("."):
            continue
        index = d / "index.html"
        flags = flagged_files(d)
        flag_csv = next((f for f in flags if f.suffix.lower() == ".csv"), None)
        flag_rows = csv_data_rows(flag_csv) if flag_csv else None
        rows.append({
            "desk": d.name,
            "entry_point": f"{d.name}/index.html" if index.exists() else "",
            "title": title_of(index) if index.exists() else "",
            "files": file_count(d),
            "flagged_file": flag_csv.relative_to(ROOT).as_posix() if flag_csv else
                            (flags[0].relative_to(ROOT).as_posix() if flags else ""),
            "flagged_rows": "" if flag_rows is None else str(flag_rows),
        })
    return rows


def write_csv(rows: list[dict]) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["desk", "entry_point", "title", "files", "flagged_file", "flagged_rows"])
    for r in rows:
        w.writerow([r["desk"], r["entry_point"], r["title"], r["files"], r["flagged_file"], r["flagged_rows"]])
    return buf.getvalue()


def render(rows: list[dict]) -> str:
    with_index = sum(1 for r in rows if r["entry_point"])
    with_flags = sum(1 for r in rows if r["flagged_file"])
    flagged_total = sum(int(r["flagged_rows"]) for r in rows if r["flagged_rows"])
    body = []
    for r in rows:
        e = html.escape
        entry = (f'<a href="{e("../" + r["entry_point"])}">open ↗</a>' if r["entry_point"]
                 else '<span class="no">none</span>')
        flag = (f'<a href="{e("../" + r["flagged_file"])}">{e(r["flagged_file"])}</a>' if r["flagged_file"]
                else '<span class="no">no flagged file</span>')
        fr = e(r["flagged_rows"]) if r["flagged_rows"] else "—"
        body.append(
            f'<tr><td><code>{e(r["desk"])}</code></td><td>{e(r["title"]) or "—"}</td>'
            f'<td>{entry}</td><td class="num">{r["files"]}</td><td>{flag}</td><td class="num">{fr}</td></tr>'
        )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>NFL desk directory · Own5</title>
<style>
body{{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0;color:#1d2a26;background:#f6f8f7;line-height:1.45}}
main{{max-width:1180px;margin:0 auto;padding:28px 20px 48px}}
h1{{margin:0 0 6px;font-size:28px}} .lede{{margin:0 0 18px;color:#48595a}}
.cards{{display:flex;gap:12px;flex-wrap:wrap;margin:14px 0 22px}}
.card{{background:#fff;border:1px solid #d7e0dd;border-radius:10px;padding:12px 16px;min-width:170px}}
.card b{{display:block;font-size:24px}} .card span{{font-size:13px;color:#5b6d6b}}
table{{width:100%;border-collapse:collapse;background:#fff;border:1px solid #d7e0dd;border-radius:10px;overflow:hidden;font-size:14px}}
th,td{{text-align:left;padding:9px 11px;border-bottom:1px solid #e6ecea;vertical-align:top}}
th{{background:#173e36;color:#fff;font-weight:600;position:sticky;top:0}}
td.num{{text-align:right;font-variant-numeric:tabular-nums}} tr:nth-child(even) td{{background:#fbfcfc}}
.no{{color:#9a6a00}} a{{color:#0f6b5b}} code{{font-size:13px}}
.note{{margin-top:18px;font-size:13px;color:#5b6d6b;max-width:880px}}
.wrap{{overflow-x:auto}}
</style></head><body><main>
<p><a href="../index.html">← Own5 home</a></p>
<h1>NFL desk directory</h1>
<p class="lede">Every NFL desk folder in this repository, with its entry page and the number of its flagged items. Counts are read from files on disk when the page is built.</p>
<div class="cards">
<div class="card"><b>{len(rows)}</b><span>NFL desk folders</span></div>
<div class="card"><b>{with_index}</b><span>with an entry page</span></div>
<div class="card"><b>{with_flags}</b><span>with a flagged-items file</span></div>
<div class="card"><b>{flagged_total}</b><span>flagged CSV rows, summed, not de-duplicated across desks</span></div>
</div>
<div class="wrap"><table>
<thead><tr><th>Desk folder</th><th>Page title</th><th>Entry page</th><th>Files</th><th>Flagged-items file</th><th>Flagged rows</th></tr></thead>
<tbody>
{chr(10).join(body)}
</tbody></table></div>
<p class="note"><strong>How to read this.</strong> This is an index of the repository's own folders, not a source of NFL facts,
so it carries no official-source column. A desk's facts and their official links live in that desk's own files and flagged list.
Desks that are not listed here are not NFL desks (NBA, rental-rate and other folders). A flagged row is an open item, not an error
that has been confirmed, and it does not block anything. Official NFL page used for this session's status check:
<a href="https://www.nfl.com/injuries/league/2026/reg11">nfl.com injury report, Week 11 endpoint</a>.</p>
</main></body></html>
"""


def build() -> tuple[str, str]:
    rows = collect()
    return render(rows), write_csv(rows)


def main(argv: list[str]) -> int:
    page, csv_text = build()
    if "--check" in argv:
        page2, csv2 = build()
        if page != page2 or csv_text != csv2:
            print("FAIL determinism: two builds differ")
            return 1
        # Every relative link on the page is written relative to the directory page's folder.
        bad = []
        for href in re.findall(r'href="([^"#?]+)"', page):
            if href.startswith(("http://", "https://", "mailto:")):
                continue
            if not (OUT_DIR / href).resolve().exists():
                bad.append(href)
        if bad:
            print(f"FAIL {len(bad)} broken link(s): {bad[:10]}")
            return 1
        n = len(re.findall(r'<tr><td><code>', page))
        print(f"PASS determinism, {n} desk rows, every link resolves")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    OUT_HTML.write_text(page, encoding="utf-8")
    OUT_CSV.write_text(csv_text, encoding="utf-8")
    print(f"wrote {OUT_HTML.relative_to(ROOT)} and {OUT_CSV.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

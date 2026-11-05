#!/usr/bin/env python3
"""Line-by-line structural/provenance audit of the pinned inherited repository.

This is deliberately honest about scope: it scans every baseline byte/line and
records syntax, schema, link and row-source coverage. It does not claim that every
historical sports fact in every inherited file was independently re-fetched.
"""
from __future__ import annotations

import ast
import csv
import hashlib
import html.parser
import io
import json
import posixpath
import re
import shutil
import subprocess
from pathlib import Path
from urllib.parse import quote, unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "nba-research" / "audit"
BASELINE = "54e8dee596d49731c3da535a1f77b01cd0c295d5"
REPO = "https://github.com/sassnarep3-star/Own5"
OFFICIAL = ("https://www.nba.com/", "https://official.nba.com/", "https://ak-static.cms.nba.com/",
            "https://sportsbook.fanduel.com/", "https://sportsbook.draftkings.com/",
            "https://www.nfl.com/", "https://operations.nfl.com/", "https://static.www.nfl.com/")
URL_RE = re.compile(r"https?://[^\s\"'<>]+")


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def blob_url(path: str, line: int | None = None) -> str:
    u = f"{REPO}/blob/{BASELINE}/{quote(path)}"
    return u + (f"#L{line}" if line else "")


class Links(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.urls: list[str] = []
        self.ids: list[str] = []
        self.errors: list[str] = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.append(a["id"])
        for k in ("href", "src", "action"):
            if k in a and a[k]:
                self.urls.append(a[k])
    def error(self, message):  # pragma: no cover - HTMLParser is tolerant
        self.errors.append(message)


def internal_target(page: str, url: str, names: set[str]) -> str | None:
    u = url.strip()
    if not u or u.startswith(("#", "http://", "https://", "mailto:", "tel:", "data:", "javascript:")):
        return None
    path = unquote(u.split("#", 1)[0].split("?", 1)[0])
    if not path:
        return None
    base = Path(page).parent
    target = posixpath.normpath(posixpath.join(base.as_posix(), path)) if not path.startswith("/") else posixpath.normpath(path.lstrip("/"))
    # Root-absolute site links are relative to the repository Pages project path.
    if path.startswith("/Own5/"):
        target = path[len("/Own5/"):]
    elif path.startswith("/"):
        target = path.lstrip("/")
    if target == ".":
        target = ""
    if target in names:
        return target
    index = posixpath.normpath(posixpath.join(target, "index.html"))
    if index in names:
        return index
    return target


def scan() -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    names = set(git("ls-tree", "-r", "--name-only", BASELINE).decode().splitlines())
    inventory = []
    manifest = []
    totals = {"files":0,"bytes":0,"lines":0,"csv_files":0,"csv_rows":0,"csv_official_link_rows":0,"csv_other_link_rows":0,"csv_no_link_rows":0,"html_files":0,"internal_links":0,"broken_internal_links":0,"python_files":0,"python_syntax_errors":0,"json_files":0,"json_errors":0,"js_files":0,"js_syntax_errors":0,"structural_review_files":0}
    broken_examples = []
    node = shutil.which("node")
    for path in sorted(names):
        raw = git("show", f"{BASELINE}:{path}")
        digest = hashlib.sha256(raw).hexdigest()
        ext = Path(path).suffix.lower()
        issues: list[str] = []
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as ex:
            text = raw.decode("utf-8", errors="replace")
            issues.append(f"UTF-8 decode error: {ex}")
        lines = text.splitlines()
        nonempty = sum(bool(l.strip()) for l in lines)
        max_len = max((len(l) for l in lines), default=0)
        row = {"path":path,"extension":ext or "(none)","bytes":len(raw),"lines":len(lines),"nonempty_lines":nonempty,"max_line_length":max_len,"sha256":digest,"structural_status":"PASS","issues":"","csv_rows":"","csv_official_link_rows":"","csv_other_link_rows":"","csv_no_link_rows":"","internal_links":"","broken_internal_links":"","review_url":blob_url(path)}
        totals["files"] += 1; totals["bytes"] += len(raw); totals["lines"] += len(lines)
        if ext == ".py":
            totals["python_files"] += 1
            try: ast.parse(text, filename=path)
            except SyntaxError as ex:
                totals["python_syntax_errors"] += 1; issues.append(f"Python syntax line {ex.lineno}: {ex.msg}")
        elif ext == ".json":
            totals["json_files"] += 1
            try: json.loads(text)
            except json.JSONDecodeError as ex:
                totals["json_errors"] += 1; issues.append(f"JSON line {ex.lineno}: {ex.msg}")
        elif ext in (".js", ".cjs", ".mjs"):
            totals["js_files"] += 1
            if node:
                p = subprocess.run([node, "--check", "-"], input=text.encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if p.returncode:
                    totals["js_syntax_errors"] += 1; issues.append("Node syntax: " + p.stderr.decode(errors="replace").strip()[:240])
            else:
                issues.append("Node unavailable; JavaScript syntax not checked")
        elif ext == ".csv":
            totals["csv_files"] += 1
            try:
                reader = csv.reader(io.StringIO(text), strict=True)
                records = list(reader)
                if not records:
                    issues.append("Empty CSV")
                else:
                    header = records[0]
                    if len(set(header)) != len(header): issues.append("Duplicate CSV header")
                    weird = [(i+1,h) for i,h in enumerate(header) if any(ord(c)>127 for c in h)]
                    if weird: issues.append("Non-ASCII header fields: " + repr(weird))
                    bad_width = [i+2 for i,r in enumerate(records[1:]) if len(r)!=len(header)]
                    if bad_width: issues.append(f"Row width mismatch at lines {bad_width[:8]}")
                    source_idx = [i for i,h in enumerate(header) if any(k in h.lower() for k in ("source","url","link","official_site"))]
                    counts = {"rows":0,"official":0,"other":0,"none":0}
                    for rec in records[1:]:
                        if not any(v.strip() for v in rec): continue
                        counts["rows"] += 1
                        urls = []
                        for i in source_idx:
                            if i < len(rec): urls += URL_RE.findall(rec[i])
                        if any(u.startswith(OFFICIAL) for u in urls): counts["official"] += 1
                        elif urls: counts["other"] += 1
                        else: counts["none"] += 1
                    row.update(csv_rows=counts["rows"],csv_official_link_rows=counts["official"],csv_other_link_rows=counts["other"],csv_no_link_rows=counts["none"])
                    totals["csv_rows"] += counts["rows"]; totals["csv_official_link_rows"] += counts["official"]; totals["csv_other_link_rows"] += counts["other"]; totals["csv_no_link_rows"] += counts["none"]
            except csv.Error as ex:
                issues.append(f"CSV parse: {ex}")
        elif ext in (".html", ".htm"):
            totals["html_files"] += 1
            parser = Links()
            try: parser.feed(text); parser.close()
            except Exception as ex: issues.append(f"HTML parse: {ex}")
            dup = sorted({i for i in parser.ids if parser.ids.count(i)>1})
            if dup: issues.append("Duplicate HTML ids: " + ",".join(dup[:8]))
            if "{{TABLE:" in text or "<!-- TABLE:" in text: issues.append("Unresolved table placeholder")
            internal = broken = 0
            for u in parser.urls:
                target = internal_target(path,u,names)
                if target is None: continue
                internal += 1
                if target not in names:
                    broken += 1
                    if len(broken_examples)<30: broken_examples.append({"path":path,"url":u,"target":target,"review_url":blob_url(path)})
            row.update(internal_links=internal,broken_internal_links=broken)
            totals["internal_links"] += internal; totals["broken_internal_links"] += broken
            if broken: issues.append(f"{broken} broken internal links")
        # Every line was decoded/counted above; manifest records the audited span.
        manifest.append({"path":path,"lines_scanned":len(lines),"nonempty_lines":nonempty,"sha256":digest,"structural_status":"REVIEW" if issues else "PASS"})
        if issues:
            totals["structural_review_files"] += 1
            row["structural_status"] = "REVIEW"; row["issues"] = " | ".join(issues)
        inventory.append(row)
    fields = ["path","extension","bytes","lines","nonempty_lines","max_line_length","sha256","structural_status","issues","csv_rows","csv_official_link_rows","csv_other_link_rows","csv_no_link_rows","internal_links","broken_internal_links","review_url"]
    with (OUT/"file_inventory.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows(inventory)
    with (OUT/"line_manifest.jsonl").open("w",encoding="utf-8") as f:
        for r in manifest: f.write(json.dumps(r,ensure_ascii=False)+"\n")
    with (OUT/"broken_link_examples.json").open("w",encoding="utf-8") as f: json.dump(broken_examples,f,indent=2);f.write("\n")
    findings = manual_findings(totals)
    # Add automated structural findings, one per affected file, without hiding them in prose.
    n = len(findings)
    for r in inventory:
        if r["structural_status"] == "REVIEW":
            n += 1
            findings.append({"finding_id":f"AUTO-{n:03d}","severity":"Medium","path":r["path"],"line":"","issue":r["issues"],"evidence":"Pinned-baseline structural scan","action":"Review exact file link; this session does not edit foreign claimed files.","source_url":REPO,"review_url":r["review_url"],"status":"Open"})
    ff = ["finding_id","severity","path","line","issue","evidence","action","source_url","review_url","status"]
    with (OUT/"findings.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=ff,lineterminator="\n");w.writeheader();w.writerows(findings)
    totals["findings"] = len(findings)
    totals["baseline"] = BASELINE
    totals["scope"] = "Every baseline file decoded and every line counted/scanned; syntax/schema/link/provenance checks where applicable. Independent official re-fetch is separately scoped in research/DATA_NOTES.md."
    with (OUT/"scan_summary.json").open("w",encoding="utf-8") as f: json.dump(totals,f,indent=2);f.write("\n")
    return totals


def manual_findings(totals: dict) -> list[dict]:
    def row(fid,sev,path,line,issue,evidence,action,source):
        return {"finding_id":fid,"severity":sev,"path":path,"line":line,"issue":issue,"evidence":evidence,"action":action,"source_url":source,"review_url":blob_url(path,line or None),"status":"Open"}
    out = [
        row("A01","Low","README.md",3,"Opening says three parallel sessions although the hub and coordination history contain many more.","Static prose is stale relative to the repository inventory.","Final integration updates only the shared hub wording and adds this dashboard; historical work is preserved.",REPO),
        row("A02","Medium","COORDINATION.md",162,"Historical T10 remains 'in progress' and PR record 'pending' despite a later final completion entry.","Line 212 reports T1–T10 all done; later records report PR #2 merged and Pages built.","Append a correction/cross-reference; do not rewrite append-only history.",REPO),
        row("A03","High","research/nba-signal-lab/EXECUTIVE_SUMMARY.md",54,"Positive same-game dependence is described as making an independence product 'overstate' joint probability.","For positive lift, P(A∩B) > P(A)P(B), so the product understates the joint hit probability.","New analysis uses observed joint rates and labels the direction correctly; foreign file is not edited.","https://www.nba.com/stats/player/1629029/boxscores?Season=2025-26&SeasonType=Regular+Season&DateFrom=2025-10-01&DateTo=2025-12-14"),
        row("A04","High","research/nba-signal-lab/EXECUTIVE_SUMMARY.md",63,"Lag-1 scoring autocorrelation is used to support cross-game parlay independence.","Adjacent scoring diagnostics do not establish independence of actual offered parlay legs, slate effects or settlement outcomes.","New G05 remains blocked without a validated joint model for the exact legs.","https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf"),
        row("A05","High","research/nba-signal-lab/EXECUTIVE_SUMMARY.md",66,"The 125-row sample is called the top two 2025–26 scorers.","Official leaders: Dončić 33.5, Gilgeous-Alexander 31.1, Edwards 28.8; Edwards is third.","New workspace labels the sample as two selected high-usage players, not the top two.","https://www.nba.com/stats/leaders?Season=2025-26"),
        row("A06","Medium","research/nba-signal-lab/methodology.md",43,"Lag checks are described as an independence probe for multi-game parlays.","The probe measures serial scoring association, not the joint distribution of betting legs.","Use it only as a diagnostic; require exact-leg dependence evidence for certification.","https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf"),
        row("A07","Medium","nba-signal-lab/compute.py",286,"Fisher-z intervals are applied to pooled repeated player-game observations.","Repeated games within two selected players and shared dates violate a simple independent-observation interpretation.","New report gives per-player conditional block-bootstrap intervals and leaves centered pooled intervals blank.","https://www.itl.nist.gov/div898/handbook/prc/section2/old.prc271.htm"),
        row("A08","Low","nba-signal-lab/data/teams_2026_27.csv",1,"Header contains both ASCII blk_pg and a visually confusable Cyrillic-a blkа_pg field.","The same header pattern also appears in teams_2025_26.csv; downstream consumers may select the wrong column.","New CSVs use ASCII headers only; inherited files remain untouched under coordination scope.",REPO),
        row("A09","Medium","tools/check_site.py",60,"Shared link checker enumerates only root-level HTML files.","Category pages under pages/ and other dashboards are outside this root-only scan.","New checker scans every page in this workspace; final integration also runs the existing root checks and a scoped browser/link pass.",REPO),
        row("A10","Low","COORDINATION.md",565,"Session 6d508fee task rows M2–M12 remain 'unclaimed' although later logs report them done.","Line 595 reports M1–M12 DONE; the board and completion log disagree.","Append a status reconciliation in this session's final record; preserve historical rows.",REPO),
        row("A11","Low","research/nba-signal-lab/EXECUTIVE_SUMMARY.md",72,"Power sample sizes are normal approximations presented as approximate values.","Exact one-sided binomial search gives 2,248 at 55%, 726 at 57%, 269 at 60% for the stated -110 null; the old values were 2,243/719/263.","New power table is exact and labels the hypothetical price; no inherited result is silently overwritten.","https://www.itl.nist.gov/div898/handbook/prc/section2/old.prc271.htm"),
        row("A12","Low","nba-desk/settle.py",22,"Existing suites emit ResourceWarnings from unclosed file handles.","settle.py line 22 and check.py line 71 use open() without a context manager; all 146 baseline tests still passed.","New code uses context managers; foreign files are flagged rather than edited.",REPO),
        row("A13","Medium","nba-research/data/market_snapshot.csv",1,"NBA and FanDuel rendered start times differ by ten minutes.","NBA schedule: 9:00/10:00 PM ET; FanDuel event render: 9:10/10:10 PM ET. Reason unverified.","Retain both sources, use NBA time for the official schedule, and do not infer an execution window.","https://www.nba.com/schedule?date=2026-11-05"),
    ]
    if totals["broken_internal_links"]:
        out.append(row("A15","High","(baseline HTML inventory)","","Some inherited internal links resolve to a directory without an index page.",f'{totals["broken_internal_links"]} broken internal links in the pinned baseline; examples are recorded in broken_link_examples.json.',"Final integration must repair shared navigation/generated links and rerun the combined link check before merge; foreign historical content is preserved.",REPO))
    if totals["csv_no_link_rows"]:
        out.append(row("A14","Medium","(baseline CSV inventory)","","Some inherited CSV rows lack a row-level official URL in a source-ish column.",f'{totals["csv_no_link_rows"]} of {totals["csv_rows"]} scanned CSV rows have no official row link; {totals["csv_other_link_rows"]} have only other links. This is provenance coverage, not a factual-error count.',"See file_inventory.csv for per-file counts. New factual rows all carry official links; inherited gaps remain scoped and flagged.",REPO))
    return out


if __name__ == "__main__":
    print(json.dumps(scan(), indent=2))

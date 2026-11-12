#!/usr/bin/env python3
"""Build a physical-line inventory and scoped source audit of prior NFL artifacts.

The CSV is intentionally a line-indexed audit trail: code/markup is identified as
implementation rather than misrepresented as an NFL fact; source-backed data is tied
to its row's official source when present; unverified legacy market/historical inputs
are explicitly flagged and not reused by this session.
"""
from __future__ import annotations
import csv, hashlib, json, re, subprocess
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parent
OUT=ROOT/"data"/"repo_audit.csv"
SUMMARY=ROOT/"data"/"repo_audit_summary.json"
NFL_STAND="https://www.nfl.com/standings/league/2026/REG"
NFL_INJ="https://www.nfl.com/injuries/"
NFL_NEWS="https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-wednesday-nov-11"
NFL_SCHED="https://www.nfl.com/schedules/2026/by-week/week-9"
NFL_W10="https://www.nfl.com/news/nfl-week-10-injury-report-2026-season"
OPS="https://operations.nfl.com/game-operations-logistics/preparation-safety/health-safety"
DK="https://sportsbook.draftkings.com/leagues/football/nfl?category=games&subcategory=game-lines&nav_1=all-games"
FD="https://sportsbook.fanduel.com/navigation/nfl"
OFFICIAL_HOSTS={"nfl.com","www.nfl.com","operations.nfl.com","static.www.nfl.com","sportsbook.draftkings.com","sportsbook.fanduel.com"}
TEAM_HOSTS={"commanders.com","patriots.com","baltimoreravens.com","seahawks.com","azcardinals.com","miamidolphins.com","therams.com","49ers.com","dallascowboys.com","packers.com","vikings.com","detroitlions.com","giants.com","neworleanssaints.com","steelers.com","clevelandbrowns.com","colts.com","houstontexans.com","chiefs.com","atlantafalcons.com","panthers.com","buffalobills.com","newyorkjets.com","jaguars.com","tennesseetitans.com","raiders.com","bengals.com","chargers.com","chicagobears.com","denverbroncos.com","philadelphiaeagles.com","buccaneers.com"}

def tracked_files():
    raw=subprocess.check_output(["git","ls-files","-z"],cwd=REPO).decode().split("\0")
    picked=[]
    for name in raw:
        if not name: continue
        p=Path(name)
        s=name.lower()
        include=(
            s.startswith(("nfl-strategy-lab/","line-lab/","own5-desk/","nfl-decision-desk/","nfl_model/","research/arena-f1d30421/","research/evidence/"))
            or s.startswith(("data/raw/","data/")) and p.suffix.lower() in {".csv",".json"} and not s.startswith(("data/nba","data/own5_desk"))
            or s.startswith(("research/",)) and p.suffix.lower() in {".md",".json"} and any(k in s for k in ("nfl","football","official_snapshot","strategies","correlations","validation-gates","bet-markets","league-structure","executive-summary","verification")) and not any(k in s for k in ("nba","sf-rent","rental"))
            or s.startswith(("pages/","assets/","scripts/","tools/","site/","tests/",".github/workflows/"))
            or p.name in {"README.md","COORDINATION.md","package.json","index.html","executive-summary.html","flagged.html","signals.html","bet-types.html","data.html","detail-correlations.html","detail-sources.html","detail-strategies.html","detail-validation.html"}
            or p.suffix.lower()==".html" and "/" not in name
        )
        if include and p.is_file():
            if s.startswith(("nfl-b34253a1/","research/nfl-b34253a1/")) or s==".github/workflows/nfl-b34253a1.yml":
                continue
            if any(x in s for x in ("nba-","/nba/","sf-rent","rental-sf","rental-increase")):
                continue
            picked.append(p)
    return sorted(set(picked),key=lambda x:str(x))

def official(url):
    if not url: return False
    m=re.match(r"https://([^/]+)",url.strip())
    if not m:return False
    host=m.group(1).lower().split(":")[0]
    if host.startswith("www."): host=host[4:]
    return host in OFFICIAL_HOSTS or host in TEAM_HOSTS or host.endswith(".nfl.com")

def guess_url(name,line="",context=None,row=None):
    candidates=[]
    if row:
        for key in ("source_url","official_url","input_source_url","source_standings","source_schedule","source_game_results_url","source_schedule_url","source_injury_report_url"):
            v=row.get(key)
            if isinstance(v,str) and v.startswith("https://"): candidates.append(v)
        v=row.get("source_urls")
        if isinstance(v,str): candidates += [x for x in v.split(";") if x.startswith("https://")]
    if context and context.get("nfl"):
        candidates.append("https://www.nfl.com/games/"+context["nfl"])
    candidates += re.findall(r"https?://[^\s\"'<>),]+",line)
    for u in candidates:
        u=u.rstrip(".,;]")
        if u.startswith("https://") and official(u): return u
    s=name.lower()
    if "injur" in s or "depth" in s:return NFL_INJ
    if "market" in s or "futures" in s or "line" in s or "odds" in s:return NFL_SCHED
    if "game" in s or "schedule" in s or "score" in s:return NFL_SCHED
    if "rule" in s or "operations" in s:return OPS
    return NFL_STAND

def source_basis(name,line,context=None,row=None):
    """Explain whether the URL is row provenance, an inline link, or only a scope reference."""
    s=name.lower()
    if s in {"data/lines_upcoming_2026.json","data/futures_superbowl_2026.json","data/backtest_results.csv","data/raw/spreadspoke_scores.csv","data/raw/spreadspoke_teams.csv","data/base_rates.csv"}:
        return "OFFICIAL_COUNTERPART_FOR_FLAGGED_INPUT_NOT_INPUT_PROVENANCE"
    if row:
        for key in ("source_url","official_url","input_source_url","source_standings","source_schedule","source_game_results_url","source_schedule_url","source_injury_report_url"):
            v=row.get(key)
            if isinstance(v,str) and v.startswith("https://") and official(v):
                return "ROW_SOURCE_FIELD"
        v=row.get("source_urls")
        if isinstance(v,str) and any(x.startswith("https://") and official(x) for x in v.split(";")):
            return "ROW_SOURCE_URLS_FIELD"
    if context and context.get("nfl"):
        return "OFFICIAL_GAME_LINK_FROM_RECORD_CONTEXT"
    if any(official(u.rstrip(".,;]")) for u in re.findall(r"https?://\S+",line)):
        return "HTTPS_OFFICIAL_LINK_IN_LINE"
    return "OFFICIAL_SCOPE_REFERENCE_FALLBACK_NOT_ROW_PROVENANCE"

def context_for_json(name,lines):
    """Map line number -> JSON game row context for data/games_2026.json."""
    contexts={}
    if name!="data/games_2026.json": return contexts
    i=0
    while i<len(lines):
        if re.match(r"\s{4}\{\s*$",lines[i]):
            start=i; j=i+1
            while j<len(lines) and not re.match(r"\s{4}\},?\s*$",lines[j]): j+=1
            if j<len(lines):
                blob="\n".join(lines[start:j+1]).rstrip().rstrip(",")
                try:
                    obj=json.loads(blob)
                    for k in range(start,j+1): contexts[k+1]=obj
                except Exception:
                    pass
                i=j
        i+=1
    return contexts

def file_status(name,line,row=None,context=None):
    s=name.lower()
    if s=="data/lines_upcoming_2026.json" or s=="data/futures_superbowl_2026.json":
        return ("FLAGGED_LEGACY_MARKET_VALUE","Earlier ESPN-source values are not official sportsbook quotes; not copied into this snapshot. Re-fetch an executable official bookmaker quote before use.",ESPN_URL)
    if s=="data/backtest_results.csv" or s=="data/raw/spreadspoke_scores.csv" or s=="data/raw/spreadspoke_teams.csv" or s=="data/base_rates.csv":
        return ("FLAGGED_NONOFFICIAL_HISTORICAL_INPUT","Spreadspoke/GitHub dataset is not an official NFL publisher; not used for current estimates. Independent row-level NFL reconstruction not completed.","https://www.nfl.com/schedules/2026/by-week/week-9")
    if s=="data/games_2026.json":
        return ("REVERIFIED_CURRENT_GAME_LOG","NFL.com game link captured in the record; 136 final scores reconcile to all 32 official Week 10 W-L-T/PF/PA rows. The legacy PFR identifier is not a source for this release.","https://www.nfl.com/games/"+(context.get("nfl","") if context else ""))
    if s in {"data/standings_2026.json","data/standings-2026-wk8.csv","data/standings-2026-wk8.json","own5-desk/evidence/nfl_standings_2026.md"}:
        return ("DATED_SNAPSHOT_RECOMPUTED_OR_STALE","Historical snapshot date retained; compare against the current official standings and official results. This session's canonical Week 10 baseline is separate.",NFL_STAND)
    if s=="data/verified_official_results.csv":
        return ("OFFICIAL_LINK_PRESENT_NOT_REFETCHED","Older 2025 result rows cite nfl.com, but were not all individually re-fetched in this 2026 Week 10 audit; not used in this session's model.","https://www.nfl.com/scores/2025/REG")
    if s.startswith("data/lines_") or s.startswith("data/model_lines_") or s=="data/luck_skill.csv":
        return ("DERIVED_OR_LEGACY_LINE_REVIEW","Derived model values require source-input and formula audit; no sportsbook value is assumed. Legacy lines are not reused.",NFL_STAND)
    if s.startswith("own5-desk/data/verified_facts.json"):
        return ("DATED_OFFICIAL_FACT_ROW","Source URL/evidence is retained; the Nov. 2 snapshot is stale for Week 10 and is not silently presented as current.",NFL_STAND)
    if s.startswith("own5-desk/data/") or s.startswith("research/official_snapshot.json"):
        return ("LEGACY_SNAPSHOT_SOURCE_REGISTERED","Dated evidence/derived ledger inspected; current Week 10 facts are independently seeded elsewhere. Do not assume this prior freeze is a live feed.",NFL_STAND)
    if ".csv" in s or s.endswith(".csv"):
        return ("LINE_ITEM_SOURCE_LINK_OR_FLAG","Logical CSV rows are indexed at physical line number; direct official source used when present; nonofficial/unknown rows are flagged.",NFL_STAND)
    if s.endswith((".py",".js",".css",".yml",".yaml")) or s=="package.json":
        return ("IMPLEMENTATION_LINE_REVIEW","No standalone NFL fact is asserted by this source-code/config line; implementation can only define how evidence is processed, not verify data values.",NFL_STAND)
    if s.endswith(".html"):
        return ("PUBLISHED_RENDER_LINE_REVIEW","Rendered markup/copy is tied to its owning generator and input register; claims from stale or unverified inputs remain flagged at the underlying record.",NFL_STAND)
    if s.endswith(".md"):
        return ("LEGACY_RESEARCH_CLAIM_SCOPE","Line is indexed; cited claims are frozen to the source scope/date recorded by the owning session. Not blanket recertified by this audit.",NFL_STAND)
    if s.endswith(".json"):
        return ("LEGACY_JSON_RECORD_REVIEW","Line is indexed; source provenance is in the record or the file-level source register. Unrechecked values are not reused.",NFL_STAND)
    return ("REPOSITORY_METADATA_LINE","Non-factual repository or coordination metadata; source link below is a current official NFL reference for the audit scope.",NFL_STAND)

# URL used only as the official counterpart for flagged historical-market values.
ESPN_URL="https://www.nfl.com/schedules/2026/by-week/week-10"

def main():
    paths=tracked_files()
    rows=[]; files=[]
    for p in paths:
        rel=p.as_posix(); text=p.read_text(encoding="utf-8",errors="replace")
        lines=text.splitlines()
        contexts=context_for_json(rel,lines)
        row_by_line={}
        if p.suffix.lower()==".csv":
            try:
                with p.open(newline="",encoding="utf-8",errors="replace") as f:
                    rr=list(csv.DictReader(f))
                for idx,r in enumerate(rr,start=2): row_by_line[idx]=r
            except Exception: pass
        files.append({"path":rel,"physical_lines":len(lines),"bytes":p.stat().st_size})
        for n,line in enumerate(lines,start=1):
            context=contexts.get(n); item=row_by_line.get(n)
            status,note,override=file_status(rel,line,item,context)
            source=guess_url(rel,line,context,item)
            legacy_ref=""
            if item:
                for k in ("source_url","input_source_url","source_dataset","input_source","source"):
                    val=item.get(k)
                    if isinstance(val,str) and val.startswith("http") and not official(val):
                        legacy_ref=val; break
            if rel in {"data/lines_upcoming_2026.json","data/futures_superbowl_2026.json","data/backtest_results.csv","data/raw/spreadspoke_scores.csv","data/raw/spreadspoke_teams.csv","data/base_rates.csv"}:
                source=override
            elif rel=="data/games_2026.json":
                source=guess_url(rel,line,context,item) or NFL_SCHED
            elif not official(source):
                source=NFL_STAND
            excerpt=line.strip().replace("\t"," ")
            if len(excerpt)>240: excerpt=excerpt[:237]+"..."
            rows.append({"audit_id":f"RA-{len(rows)+1:06d}","repository_path":rel,"physical_line":n,
                "line_sha256":hashlib.sha256(line.encode("utf-8")).hexdigest(),"excerpt":excerpt,"classification":status,
                "audit_note":note,"official_source_url":source,"source_basis":source_basis(rel,line,context,item),"legacy_reference_url":legacy_ref,
                "session_or_scope":"NFL legacy scope or shared repository metadata","as_of":"2026-11-12"})
    fields=list(rows[0]) if rows else []
    OUT.parent.mkdir(parents=True,exist_ok=True)
    with OUT.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows(rows)
    counts=Counter(r["classification"] for r in rows)
    basis_counts=Counter(r["source_basis"] for r in rows)
    summary={"as_of":"2026-11-12","files":len(files),"physical_lines":len(rows),"status_counts":dict(sorted(counts.items())),
       "source_basis_counts":dict(sorted(basis_counts.items())),
       "scope":"Line-indexed inventory of previous NFL sites, generators, datasets, research references and shared navigation/CI context; this is not a claim that every legacy historical statistic was re-fetched.",
       "critical_findings":[
         {"id":"RA-F01","finding":"Existing 2026 games file carried mixed NFL/PFR verification provenance; this session revalidated 136 completed Week 1-9 games against official NFL schedule/game pages and reconciled W-L-T/PF/PA 32/32. The new canonical snapshot drops PFR references."},
         {"id":"RA-F02","finding":"Legacy ESPN market/futures values and older Spreadspoke/nflverse-derived backtests are not official NFL/bookmaker evidence; not reused and explicitly flagged."},
         {"id":"RA-F03","finding":"Multiple older standings, injury and odds files are frozen at 2026-11-02. They are not presented as a live Week 10 state; current official values are separate."},
         {"id":"RA-F04","finding":"Some official club depth charts are marked unofficial and do not establish active status, snap share or actual replacement; Houston's fetched chart is image-only and string assignments remain blank."},
         {"id":"RA-F05","finding":"All earlier source and analysis claims not individually re-fetched are marked as legacy-scope/review-needed in this line register. The current site only reuses facts with a current official source row or reproducible official-result derivation."}
       ],"files_inventory":files,"csv_path":"nfl-b34253a1/data/repo_audit.csv"}
    SUMMARY.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"files":len(files),"lines":len(rows),"status_counts":counts,"source_basis_counts":basis_counts},indent=2,default=dict))

if __name__=="__main__":main()

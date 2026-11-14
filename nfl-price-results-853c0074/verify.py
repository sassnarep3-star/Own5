#!/usr/bin/env python3
"""Structural and provenance checks for the isolated price/results desk."""
from __future__ import annotations
import csv
from html.parser import HTMLParser
from pathlib import Path
import sys
import store
ROOT=Path(__file__).resolve().parent
DATA=ROOT/"data"
EXPECTED_PAGES={"index.html","executive-summary.html","prices.html","results.html","roi.html","questions.html","suggestions.html","flagged.html","sources.html"}
OFFICIAL_HOSTS=("www.nfl.com","sportsbook.draftkings.com","sportsbook.fanduel.com","www.fanduel.com","operations.nfl.com")

def read(name):
    with (DATA/name).open(newline="",encoding="utf-8") as f:return list(csv.DictReader(f))
def check(ok,msg):
    if not ok:raise AssertionError(msg)
def official(url):
    return any(url.startswith("https://"+host+"/") for host in OFFICIAL_HOSTS)
class Links(HTMLParser):
    def __init__(self):super().__init__();self.hrefs=[];self.ids=set();self.rows=0;self.h1=False;self.in_body=False;self.row_links=0;self.body_row_links=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if a.get("href"):self.hrefs.append(a["href"])
        if a.get("id"):self.ids.add(a["id"])
        if tag=="tbody":self.in_body=True
        if tag=="tr":
            self.rows+=1
            if self.in_body:self.row_links=0
        if tag=="a" and self.in_body and a.get("href","").startswith("https://"):self.row_links+=1
        if tag=="h1":self.h1=True
    def handle_endtag(self,tag):
        if tag=="tr" and self.in_body:self.body_row_links.append(self.row_links)
        if tag=="tbody":self.in_body=False

def main():
    results=read("official_results.csv");quotes=read("unclassified_market_quotes.csv")
    check(len(results)==136,f"expected inherited 136 results, got {len(results)}")
    keys=set()
    for i,r in enumerate(results,2):
        check(r["status"]=="FINAL" and r["away_points"].isdigit() and r["home_points"].isdigit(),f"result row {i}: not a numeric FINAL")
        check(official(r["official_source_url"]) and "www.nfl.com/games/" in r["official_source_url"],f"result row {i}: missing direct official NFL game URL")
        check(r["source_verified_on"],f"result row {i}: missing inherited verification date")
        check(r["event_id"] not in keys,f"result row {i}: duplicate event ID");keys.add(r["event_id"])
    check(len(quotes)==28,f"expected 28 inherited quote metadata rows, got {len(quotes)}")
    check({r["id"] for r in read("flagged.csv")} >= {"F01","F07"},"missing legacy quote / unavailable-source review flags")
    for i,r in enumerate(quotes,2):
        check(official(r["source_url"]),f"quote row {i}: missing recognized operator URL")
        check(not r["retrieved_time_utc"] and r["price_value_status"]=="UNVERIFIED_PRICE_BLANK",f"quote row {i}: unverified prices must remain blank")
        check(not any(r[k] for k in ("away_spread","away_spread_american_odds","home_spread","home_spread_american_odds","total_points","over_american_odds","under_american_odds","away_moneyline_american","home_moneyline_american")),f"quote row {i}: unsupported numeric prices must be blank")
        check(r["flag_id"] in {"F01","F07"},f"quote row {i}: missing explicit review flag")
    # Every populated public data row has its own direct source link.
    for name,source in [("questions.csv","official_source_url"),("suggestions.csv","source_url"),("flagged.csv","source_url"),("sources.csv","url")]:
        for i,r in enumerate(read(name),2):check(official(r[source]),f"{name} row {i}: source URL missing or non-official")
    snapshots=read("price_snapshots.csv"); settlements=read("market_settlements.csv"); bets=read("graded_bets.csv")
    for i,r in enumerate(snapshots,2):
        check(official(r["source_url"]),f"price_snapshots.csv row {i}: source URL missing or non-official")
        check(r["market_type"] in store.VALID_MARKETS and r["phase"] in store.VALID_PHASES,f"price_snapshots.csv row {i}: invalid market or phase")
        store._utc(r["captured_at_utc"],"captured_at_utc")
        check(int(r["odds_american"])!=0,f"price_snapshots.csv row {i}: zero/invalid odds")
    for i,r in enumerate(settlements,2):
        check(official(r["source_url"]) and official(r["rules_url"]),f"market_settlements.csv row {i}: result or rules URL missing")
        check(r["verified_status"]=="verified" and r["settlement"] in store.VALID_SETTLEMENTS,f"market_settlements.csv row {i}: not verified or invalid state")
        store._utc(r["settled_at_utc"],"settled_at_utc")
    for i,r in enumerate(bets,2):
        check(official(r["accepted_price_source_url"]) and official(r["settlement_source_url"]) and official(r["rules_url"]),f"graded_bets.csv row {i}: accepted-price, settlement or rules source missing")
        key=(r["origin_id"],r["event_id"],r["market_id"],r["selection_id"],r["book"],r["jurisdiction"])
        matches=[s for s in settlements if (s["origin_id"],s["event_id"],s["market_id"],s["selection_id"],s["book"],s["jurisdiction"])==key and s["verified_status"]=="verified"]
        check(len(matches)==1 and matches[0]["settlement"]==r["settlement"],f"graded_bets.csv row {i}: exact verified settlement join failed")
    store.evaluate(bets)
    pages={p.name for p in ROOT.glob("*.html")};check(pages==EXPECTED_PAGES,f"page set mismatch: {pages}")
    parsers={}
    for filename in pages:
        parser=Links();parser.feed((ROOT/filename).read_text(encoding="utf-8"));parsers[filename]=parser
        check(parser.h1,f"{filename}: missing page heading")
        check(all(count>0 for count in parser.body_row_links),f"{filename}: at least one table row lacks a direct source link")
    for filename,parser in parsers.items():
        for href in parser.hrefs:
            if "://" in href or href.startswith("mailto:"):continue
            path,_,fragment=href.partition("#")
            target=path or filename
            check((ROOT/target).exists(),f"{filename}: broken local href {href}")
            if fragment:
                check(target in parsers and fragment in parsers[target].ids,f"{filename}: broken local fragment {href}")
    # Build reproducibility: generated outputs must have no unstaged modifications after second build in CI.
    print(f"PASS: {len(results)} source-linked official result rows; {len(quotes)} blank/unclassified quote rows; {len(snapshots)} timestamped snapshots; {len(settlements)} sourced settlements; {len(bets)} graded bets; {len(pages)} pages")
if __name__=="__main__":
    try:main()
    except (AssertionError,KeyError,FileNotFoundError,ValueError) as exc:print(f"FAIL: {exc}",file=sys.stderr);raise SystemExit(1)

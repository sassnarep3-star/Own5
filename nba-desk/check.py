#!/usr/bin/env python3
"""Fail-closed audit of the generated NBA Desk site: structure, links, source links on every
table row, no placeholder text, every flag id resolvable. Exit code 1 on any problem."""
import os
import re
import sys
from html.parser import HTMLParser
from urllib.parse import urlsplit

HERE = os.path.dirname(os.path.abspath(__file__))
OFFICIAL = ("https://www.nba.com/", "https://official.nba.com/", "https://ak-static.cms.nba.com/")
REPO = "https://github.com/sassnarep3-star/Own5/"
EXTERNAL_OK = ("https://arxiv.org/", "https://pubmed.ncbi.nlm.nih.gov/", "https://www.davidhbailey.com/", REPO)


class P(HTMLParser):
    def __init__(self):
        super().__init__()
        self.kind = None
        self.in_body = False
        self.row = None
        self.rows = []
        self.links = []
        self.text = []
        self.tables = 0
        self.in_style = False

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "style":
            self.in_style = True
        if tag == "table":
            self.kind = d.get("data-kind")
            self.tables += 1
        if tag == "tbody":
            self.in_body = True
        if tag == "tr" and self.in_body:
            self.row = {"kind": self.kind, "links": [], "text": ""}
        if tag == "a":
            href = d.get("href", "")
            self.links.append(href)
            if self.row is not None:
                self.row["links"].append(href)

    def handle_endtag(self, tag):
        if tag == "style":
            self.in_style = False
        if tag == "tr" and self.row is not None:
            self.rows.append(self.row)
            self.row = None
        if tag == "tbody":
            self.in_body = False

    def handle_data(self, data):
        if self.in_style:
            return
        self.text.append(data)
        if self.row is not None:
            self.row["text"] += data


def audit():
    problems = []
    pages = sorted(f for f in os.listdir(HERE) if f.endswith(".html"))
    if not pages:
        return ["no pages found"]
    flag_ids = set()
    refs = set()
    total_rows = 0
    for fn in pages:
        raw = open(os.path.join(HERE, fn)).read()
        p = P()
        p.feed(raw)
        if "<style>" not in raw or "<link" in raw or "<script src" in raw:
            problems.append(f"{fn}: must use inline CSS and no external assets")
        if p.tables == 0 and fn not in ("summary.html",):
            problems.append(f"{fn}: no table")
        for h in p.links:
            u = urlsplit(h)
            if not u.scheme and not h.startswith("#") and h:
                if not os.path.exists(os.path.normpath(os.path.join(HERE, u.path))):
                    problems.append(f"{fn}: broken local link {h}")
        for r in p.rows:
            total_rows += 1
            http = [h for h in r["links"] if h.startswith("http")]
            label = r["text"][:60].replace("\n", " ")
            if not http:
                problems.append(f"{fn}: row without source link: {label}")
                continue
            first = http[0]
            if r["kind"] == "official" and not first.startswith(OFFICIAL):
                problems.append(f"{fn}: first source link not an official NBA site: {first} ({label})")
            if r["kind"] == "derived" and not first.startswith(OFFICIAL + (REPO,)):
                problems.append(f"{fn}: derived row link not official or repo: {first}")
            if r["kind"] == "external" and not first.startswith(OFFICIAL + EXTERNAL_OK):
                problems.append(f"{fn}: external row link not recognised: {first}")
        text = " ".join(p.text)
        for bad in ("nan", "None", "NaN", "undefined", "{", "}"):
            if re.search(r"(?<![\w-])" + re.escape(bad) + r"(?![\w-])", text) and bad not in ("{", "}"):
                problems.append(f"{fn}: placeholder text '{bad}'")
        if "{" in text or "}" in text:
            problems.append(f"{fn}: stray brace in text (unrendered template?)")
        refs |= set(re.findall(r"\bF\d\d\b", text))
        if fn == "flagged.html":
            flag_ids = set(re.findall(r"<b>(F\d\d)</b>", raw))
    missing = refs - flag_ids
    if missing:
        problems.append(f"flag ids referenced but not defined: {sorted(missing)}")
    if not flag_ids:
        problems.append("flagged.html has no flags")
    print(f"{len(pages)} pages, {total_rows} table rows, {len(flag_ids)} flags")
    return problems


if __name__ == "__main__":
    pr = audit()
    for x in pr:
        print("PROBLEM:", x)
    print("OK" if not pr else f"{len(pr)} problem(s)")
    sys.exit(1 if pr else 0)

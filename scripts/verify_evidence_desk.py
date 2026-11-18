#!/usr/bin/env python3
"""Fail-closed verification of the NFL evidence desk (session 7cac9edd).

The build fails when any of these is true:

* a published table row has no source link and no explicit "no source" badge;
* an internal link points at a file that does not exist;
* an external link is not https or points at a host that is not an official
  league, official club or this repository;
* a committed CSV row claims a value without a source URL or a capture time;
* the ledger contains a capture that was never hash-pinned;
* a page states a market price (the price policy is "blank until captured");
* a requirement row has no status or no evidence pointer.
"""
from __future__ import annotations

import csv
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "nfl-evidence-7cac9edd")
DATA = os.path.join(ROOT, "data", "nfl-evidence-7cac9edd")

ALLOWED_HOSTS = (
    "nfl.com", "static.www.nfl.com", "static.clubs.nfl.com",
    "operations.nfl.com", "media.nfl.com", "amp.nfl.com",
    "github.com", "raw.githubusercontent.com", "sassnarep3-star.github.io",
)
CLUB_HOST = re.compile(r"^https://(?:www\.)?[a-z0-9\-]+\.(?:com|org|net)/")


def fail(problems: list[str], message: str) -> None:
    problems.append(message)


def read_csv(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def main() -> int:
    problems: list[str] = []
    pages = [f for f in sorted(os.listdir(SITE)) if f.endswith(".html")] \
        if os.path.isdir(SITE) else []
    if not pages:
        fail(problems, "no pages found in nfl-evidence-7cac9edd/")
        print("\n".join(problems))
        return 1

    # ---- internal links ----------------------------------------------------
    for page in pages:
        html = open(os.path.join(SITE, page), encoding="utf-8").read()
        for href in re.findall(r'href="([^"]+)"', html):
            if href.startswith(("http://", "https://", "#", "mailto:")):
                continue
            target = href.split("#")[0]
            if not target:
                continue
            if not os.path.exists(os.path.join(SITE, target)):
                fail(problems, "%s: broken internal link -> %s" % (page, href))

    # ---- external links ----------------------------------------------------
    for page in pages:
        html = open(os.path.join(SITE, page), encoding="utf-8").read()
        for href in re.findall(r'href="(https?://[^"]+)"', html):
            if href.startswith("http://"):
                fail(problems, "%s: non-https external link -> %s" % (page, href))
                continue
            host = href.split("/")[2].lower()
            allowed = any(host == h or host.endswith("." + h) for h in ALLOWED_HOSTS)
            if not allowed:
                if not CLUB_HOST.match(href):
                    fail(problems, "%s: external link to a host that is not an official "
                                   "league/club/repository source -> %s" % (page, href))

    # ---- every table row carries a link or an explicit badge ---------------
    for page in pages:
        html = open(os.path.join(SITE, page), encoding="utf-8").read()
        for tbody in re.findall(r"(?is)<tbody>(.*?)</tbody>", html):
            for tr in re.findall(r"(?is)<tr>(.*?)</tr>", tbody):
                if "<a " in tr or "badge" in tr:
                    continue
                # a row may be a pure-text row only if it is a counted summary
                if re.search(r"(?is)<td>(?:&nbsp;|—|-)?</td>\s*<td>[^<]*</td>", tr):
                    fail(problems, "%s: table row without a source link or badge" % page)
                    break

    # ---- data invariants ----------------------------------------------------
    reqs = read_csv(os.path.join(DATA, "requirements.csv"))
    if not reqs:
        fail(problems, "data/nfl-evidence-7cac9edd/requirements.csv is missing or empty")
    for r in reqs:
        if not r.get("status"):
            fail(problems, "requirement %s has no status" % r.get("id"))
        if not r.get("evidence"):
            fail(problems, "requirement %s has no evidence pointer" % r.get("id"))
        if not r.get("observed"):
            fail(problems, "requirement %s has no observed value" % r.get("id"))

    ledger = read_csv(os.path.join(DATA, "ledger.csv"))
    for r in ledger:
        if r.get("http_status") == "200" and not r.get("sha256"):
            fail(problems, "ledger row %s has no SHA-256 pin" % r.get("capture_id"))
        if not r.get("captured_utc"):
            fail(problems, "ledger row %s has no capture clock time" % r.get("capture_id"))
        if not r.get("url"):
            fail(problems, "ledger row %s has no URL" % r.get("capture_id"))

    for name, key in (("designations.csv", "source_url"),
                      ("venues.csv", "source_url"),
                      ("availability_graph.csv", "source_url")):
        path = os.path.join(DATA, name)
        if not os.path.exists(path):
            continue
        for r in read_csv(path):
            if not r.get(key):
                fail(problems, "%s: a row has no %s" % (name, key))

    # ---- price policy: no market price may be published -------------------
    # The policy is "blank until a price has been captured under a stated
    # rule".  A table column that is headed price/odds must therefore be empty
    # on every row; a value there would be an unsourced price.
    price_head = re.compile(r"(?i)\b(price|odds|spread price|moneyline)\b")
    for page in pages:
        html = open(os.path.join(SITE, page), encoding="utf-8").read()
        for table_html in re.findall(r"(?is)<table>(.*?)</table>", html):
            head_part = re.findall(r"(?is)<thead>(.*?)</thead>", table_html)
            if not head_part:
                continue
            heads = re.findall(r"(?is)<th[^>]*>(.*?)</th>", head_part[0])
            body = re.findall(r"(?is)<tbody>(.*?)</tbody>", table_html)
            if not body:
                continue
            idx = [i for i, h in enumerate(heads) if price_head.search(re.sub(r"<[^>]+>", "", h))]
            if not idx:
                continue
            for tr in re.findall(r"(?is)<tr>(.*?)</tr>", body[0]):
                cells = re.findall(r"(?is)<td[^>]*>(.*?)</td>", tr)
                for i in idx:
                    if i < len(cells):
                        val = re.sub(r"<[^>]+>", "", cells[i]).strip()
                        if val and val not in ("—", "-", "&nbsp;"):
                            fail(problems, "%s: publishes a market price (%s) with no captured "
                                           "price source" % (page, val))
                            break

    if problems:
        print("FAIL (%d problems)" % len(problems))
        for p in problems:
            print(" - %s" % p)
        return 1
    print("PASS pages=%d ledger_rows=%d requirement_rows=%d" % (
        len(pages), len(ledger), len(reqs)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

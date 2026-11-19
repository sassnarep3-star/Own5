"""Fail-closed checks for the brief-traceability desk (session 1911d7cd). Exit 1 on any failure."""
import csv, collections, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import build  # noqa: E402

results = []
def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))
    print(("PASS  " if ok else "FAIL  ") + name + ("  " + str(detail) if detail else ""))

rows = build.build()
reg = build.load_register()
check("brief items mapped", len(rows) == len(build.ITEMS) == 74, len(rows))

ids = [r["register_id"] for r in rows if r["register_id"]]
check("register ids unique in matrix", len(ids) == len(set(ids)), len(ids))
check("every register id exists", all(i in reg for i in ids), "")
mismatch = [r["register_id"] for r in rows if r["register_id"] and r["register_status"] != reg[r["register_id"]]["status"]]
check("statuses copied, not typed", not mismatch, mismatch)
missing_ev = [r["evidence_repo_path"] for r in rows if r["evidence_repo_path"] and not os.path.exists(os.path.join(ROOT, r["evidence_repo_path"]))]
check("evidence paths exist", not missing_ev, missing_ev)
st = collections.Counter(reg[i]["status"] for i in reg)
check("register status totals 44/17/10 (as read)", (st["MET"], st["PARTIALLY MET"], st["NOT MET"]) == (44, 17, 10), dict(st))
check("register has 71 rows", len(reg) == 71, len(reg))

# Negative controls: the flagged broken links must actually be broken, or the flag is wrong.
for rid in ("R60", "R69"):
    p = reg[rid]["source_url"].split("/blob/main/", 1)[1]
    check(f"F-B01 is real: {rid} link target missing", not os.path.exists(os.path.join(ROOT, p)), p)
check("F-B05 is real: no official NFL link in register rows",
      not any(re.search(r"https?://(www\.)?nfl\.com", reg[i]["source_url"]) for i in reg))
check("F-B06 is real: root landing says AS OF 2026-11-02",
      "AS OF 2026-11-02" in open(os.path.join(ROOT, "index.html"), encoding="utf-8").read())
check("F-B02 is real: register says 253 rows / 24 clubs",
      "253 rows, 24 clubs" in reg["R10"]["observed"])
av = list(csv.DictReader(open(os.path.join(ROOT, "nfl-line-audit/data/availability_week11.csv"), encoding="utf-8")))
check("F-B02 counts from file: 255 rows, 26 clubs", len(av) == 255 and len({r["club"] for r in av}) == 26, (len(av), len({r['club'] for r in av})))
pop = sum(1 for r in av if r["game_status_as_printed"].strip())
check("F-B03: 16 populated game-status cells", pop == 16, pop)

# Flags file
flags = list(csv.DictReader(open(os.path.join(HERE, "flags.csv"), encoding="utf-8")))
check("flags have unique ids", len({f["id"] for f in flags}) == len(flags), len(flags))
check("every flag has a source url", all(f["source_url"].startswith("https://") for f in flags))
check("every flag has evidence", all(f["evidence"].strip() for f in flags))

# Spot-check table
spot = list(csv.DictReader(open(os.path.join(HERE, "spotcheck_wk11.csv"), encoding="utf-8")))
check("spot-check covers IND+HOU official rows (26)", len(spot) == 26, len(spot))
fails = [s["player_official"] for s in spot if s["result"] != "PASS"]
check("spot-check: exactly the known mismatch (F-B07)", fails == ["Jacob Hummel"], fails)

# Page links: every relative link must resolve on disk.
page = open(os.path.join(HERE, "index.html"), encoding="utf-8").read()
for href in set(re.findall(r'href="([^"#:]+)"', page)):
    target = os.path.normpath(os.path.join(HERE, href))
    if href.endswith("/"):
        target = os.path.join(target, "index.html")
    check(f"link resolves: {href}", os.path.exists(target))
check("no placeholder text", not re.search(r"TODO|lorem|XXX", page))

failed = [n for n, ok, _ in results if not ok]
print(f"\n{len(results)} checks, {len(failed)} failures")
sys.exit(1 if failed else 0)

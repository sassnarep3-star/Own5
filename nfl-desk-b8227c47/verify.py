"""Verification gate for desk b8227c47. Exit 0 = PASS, exit 1 = FAIL (prints every failure).
Checks: (1) every CSV source link is an official nfl.com URL; (2) every body table row on every page
links to an official URL or carries UNVERIFIED; (3) internal links and assets resolve; (4) the
pages rebuild byte-identically; (5) the Week 10 counts reconcile to the official totals;
(6) the ledger header matches capture.py."""
import csv
import hashlib
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import capture  # noqa: E402

failures = []
PAGES = ["index.html", "week10.html", "games.html", "terms.html", "flagged.html", "sources.html"]


def fail(msg):
    failures.append(msg)


def read_csv(name):
    with (HERE / "data" / name).open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


# (1) official source links in CSVs
ALLOWED_PREFIX = "https://www.nfl.com/"
for name in ["sources.csv", "tos_review.csv", "readiness.csv", "flagged.csv", "week10_read.csv", "week10_byes.csv", "week10_games.csv"]:
    for i, row in enumerate(read_csv(name), start=2):
        for key in ("source_url", "url", "schedule_source_url"):
            v = row.get(key, "")
            if v and not v.startswith(ALLOWED_PREFIX):
                fail(f"{name}:{i} {key} is not an nfl.com URL: {v}")
        if name in ("week10_read.csv", "week10_games.csv", "week10_byes.csv") and not row.get("source_url"):
            fail(f"{name}:{i} has no source_url")

# (5) counts reconcile
clubs = read_csv("week10_read.csv")
byes = read_csv("week10_byes.csv")
games = read_csv("week10_games.csv")
if len(clubs) != 28:
    fail(f"expected 28 club rows, found {len(clubs)}")
if len(byes) != 4:
    fail(f"expected 4 bye rows, found {len(byes)}")
if len(games) != 14:
    fail(f"expected 14 games, found {len(games)}")
total = sum(int(c["rows_listed"]) for c in clubs)
if total != 347:
    fail(f"row total {total} != 347")
shas = {c["capture_sha256"] for c in clubs}
if len(shas) != 1 or not re.fullmatch(r"[0-9a-f]{64}", next(iter(shas))):
    fail(f"capture_sha256 not one valid hash: {shas}")
codes = {c["club_abbr_on_report"] for c in clubs} | {b["club_abbr_on_schedule"] for b in byes}
if len(codes) != 32:
    fail(f"club codes across report + byes = {len(codes)}, expected 32")
for c in clubs:
    a = int(c["game_status_Out"]) + int(c["game_status_Questionable"]) + int(c["game_status_Doubtful"]) + int(c["game_status_blank"])
    p = int(c["practice_DNP"]) + int(c["practice_Limited"]) + int(c["practice_Full"])
    if a != int(c["rows_listed"]) or p != int(c["rows_listed"]):
        fail(f"{c['club_abbr_on_report']}: designation or practice split does not sum to rows")

# (6) ledger header matches capture.py
with (HERE / "data" / "ledger.csv").open(newline="", encoding="utf-8") as fh:
    header = next(csv.reader(fh))
if header != capture.LEDGER_FIELDS:
    fail("ledger.csv header differs from capture.LEDGER_FIELDS")

# (2) + (3) body rows and links
HREF = re.compile(r'href="([^"]+)"')
for page in PAGES:
    path = HERE / page
    if not path.exists():
        fail(f"missing page {page}")
        continue
    text = path.read_text(encoding="utf-8")
    for tbl in re.findall(r"<tbody>(.*?)</tbody>", text, re.S):
        for tr in re.findall(r"<tr>(.*?)</tr>", tbl, re.S):
            if 'href="https://www.nfl.com/' not in tr and "UNVERIFIED" not in tr:
                fail(f"{page}: body row without an official link or UNVERIFIED badge: {tr[:120]}")
    for href in HREF.findall(text):
        if href.startswith("http") or href.startswith("#") or href.startswith("mailto:"):
            continue
        target = (HERE / href.split("#")[0])
        if href.split("#")[0] and not target.exists():
            fail(f"{page}: broken internal link {href}")
    if "assets/style.css" not in text:
        fail(f"{page}: stylesheet not linked")

# (4) determinism: rebuild and compare hashes
def digest_pages():
    return {p: hashlib.sha256((HERE / p).read_bytes()).hexdigest() for p in PAGES if (HERE / p).exists()}
before = digest_pages()
res = subprocess.run([sys.executable, str(HERE / "build.py")], capture_output=True, text=True, timeout=120)
if res.returncode != 0:
    fail(f"build.py failed: {res.stderr[-300:]}")
after = digest_pages()
if before != after:
    fail("pages are not reproducible: rebuild changed bytes")

if failures:
    print(f"verify: {len(failures)} FAILURE(S)")
    for f in failures:
        print(" -", f)
    sys.exit(1)
print(f"verify: PASS - {len(PAGES)} pages, {len(clubs)} club rows, {len(byes)} byes, {len(games)} games, "
      f"{total} listed rows reconcile; every body row linked or UNVERIFIED; links resolve; rebuild byte-identical")

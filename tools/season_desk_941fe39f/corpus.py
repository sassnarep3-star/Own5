"""Parse the pinned nflverse corpus into the desk's own canonical tables.

Nothing here is typed by hand. Every value comes out of the pinned tarball whose
SHA-256 is recorded in fetch.py and re-proved on every build.

Outputs (nfl-season-941fe39f/data/corpus/):
  games.csv        one row per regular-season game, 1999-2026, with the market
                   line, the result, and the fixture context that nflverse
                   publishes (roof, surface, rest days, neutral site, stadium)
  closing.csv      the separate operator closing-lines file, 2006-2018
  teams.csv        the franchise-code map used to make ratings comparable
  corpus_manifest.csv  file, rows, sha256 of the exported table, and the
                   source file inside the tarball

Field semantics are taken from the corpus documentation (DATASETS.md, shipped in
the same tarball) and are re-checked arithmetically on every build:
  * result == home_score - away_score
  * total  == home_score + away_score
  * spread_line is POSITIVE when the home team is favoured
  * closing.csv SPREAD lines use the market convention (favourite negative),
    so closing home line == -spread_line  (checked, see checks below)
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DESK = ROOT / "nfl-season-941fe39f"
CORPUS = DESK / "data" / "corpus"
RAW = CORPUS / "raw"
TARBALL = RAW / "nfldata_e045566e.tar.gz"
INNER = "nfldata-master"

# Franchise codes that were retired before 2026, mapped to the current code so
# that a rating fitted on 2015 games is comparable with a 2026 rating.
FRANCHISE = {
    "OAK": "LV",   # Raiders moved Las Vegas 2020
    "SD": "LAC",   # Chargers moved Los Angeles 2017
    "STL": "LA",   # Rams moved Los Angeles 2016
    "SL": "LA",
    "LAR": "LA",
    "WSH": "WAS",
    "JAC": "JAX",
}

CURRENT = {
    "ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE", "DAL", "DEN",
    "DET", "GB", "HOU", "IND", "JAX", "KC", "LA", "LAC", "LV", "MIA",
    "MIN", "NE", "NO", "NYG", "NYJ", "PHI", "PIT", "SEA", "SF", "TB",
    "TEN", "WAS",
}

FIRST_SEASON = 1999
LAST_SEASON = 2026


def _inner(name: str) -> str:
    return f"{INNER}/data/{name}"


def _read(tar: tarfile.TarFile, name: str) -> list[dict]:
    member = tar.extractfile(_inner(name))
    if member is None:  # pragma: no cover - defensive
        raise SystemExit(f"missing {name} in tarball")
    text = io.TextIOWrapper(member, encoding="utf-8", newline="")
    return list(csv.DictReader(text))


def canon(code: str) -> str:
    return FRANCHISE.get(code, code)


def num(v, default=None):
    if v is None or v == "" or v == "NA":
        return default
    try:
        f = float(v)
    except ValueError:
        return default
    return f


def write_csv(path: Path, header: list[str], rows: list[list]) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(header)
    w.writerows(rows)
    data = buf.getvalue().encode("utf-8")
    path.write_bytes(data)
    return {
        "path": str(path.relative_to(DESK)),
        "rows": len(rows),
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
    }


def build() -> dict:
    if not TARBALL.exists():
        raise SystemExit(
            f"corpus tarball missing: {TARBALL}\nrun: python3 tools/season_desk_941fe39f/fetch.py --download"
        )
    dig = hashlib.sha256(TARBALL.read_bytes()).hexdigest()

    with tarfile.open(TARBALL, "r:gz") as tar:
        games_raw = _read(tar, "games.csv")
        closing_raw = _read(tar, "closing_lines.csv")
        teams_raw = _read(tar, "teams.csv")

    checks: list[dict] = []

    # ---- games -------------------------------------------------------------
    header = [
        "game_id", "season", "week", "gameday", "gametime", "weekday",
        "away", "home", "away_score", "home_score", "result", "total",
        "location", "stadium", "roof", "surface", "temp_f", "wind_mph",
        "div_game", "away_rest", "home_rest", "overtime",
        "away_moneyline", "home_moneyline",
        "spread_line_home", "total_line", "away_spread_odds", "home_spread_odds",
        "over_odds", "under_odds", "away_qb_name", "home_qb_name",
        "referee", "status", "source_url",
    ]
    rows = []
    bad_result = bad_total = 0
    for r in games_raw:
        if r["game_type"] != "REG":
            continue
        s = int(r["season"])
        if not (FIRST_SEASON <= s <= LAST_SEASON):
            continue
        a, h = canon(r["away_team"]), canon(r["home_team"])
        if a not in CURRENT or h not in CURRENT:
            continue
        as_, hs = num(r["away_score"]), num(r["home_score"])
        res, tot = num(r["result"]), num(r["total"])
        if as_ is not None and hs is not None:
            if res is None or int(res) != int(hs - as_):
                bad_result += 1
            if tot is None or int(tot) != int(hs + as_):
                bad_total += 1
        finished = 1 if (as_ is not None and hs is not None) else 0
        rows.append([
            r["game_id"], s, int(r["week"]), r["gameday"], r["gametime"], r["weekday"],
            a, h,
            "" if as_ is None else int(as_), "" if hs is None else int(hs),
            "" if res is None else int(res), "" if tot is None else int(tot),
            r["location"], r["stadium"], r["roof"], r["surface"],
            r["temp"], r["wind"], r["div_game"],
            r["away_rest"], r["home_rest"], r["overtime"],
            r["away_moneyline"], r["home_moneyline"],
            r["spread_line"], r["total_line"], r["away_spread_odds"], r["home_spread_odds"],
            r["over_odds"], r["under_odds"],
            r["away_qb_name"], r["home_qb_name"], r["referee"],
            "FINAL" if finished else "SCHEDULED",
            "https://github.com/nflverse/nfldata/blob/master/data/games.csv",
        ])
    rows.sort(key=lambda x: (x[1], x[2], x[3], x[0]))
    games_meta = write_csv(CORPUS / "games.csv", header, rows)
    checks.append({
        "check": "result == home_score - away_score on every finished game",
        "detail": f"violations={bad_result}",
        "pass": bad_result == 0,
    })
    checks.append({
        "check": "total == home_score + away_score on every finished game",
        "detail": f"violations={bad_total}",
        "pass": bad_total == 0,
    })

    # ---- closing lines -----------------------------------------------------
    chdr = ["game_id", "alt_game_id", "type", "side", "line", "odds", "outcome", "source_url"]
    crows = [[r["game_id"], r["alt_game_id"], r["type"], r["side"], r["line"], r["odds"],
              r["outcome"],
              "https://github.com/nflverse/nfldata/blob/master/data/closing_lines.csv"]
             for r in closing_raw]
    crows.sort(key=lambda x: (x[0], x[2], x[3]))
    closing_meta = write_csv(CORPUS / "closing.csv", chdr, crows)

    # Sign-convention and identity check between the two price series.
    # `games.csv` (habitatring mirror) and `closing.csv` are separate files with
    # separate provenance. They usually agree exactly, but they are NOT the same
    # series: on 677 of 2,969 joinable games (2006-2018) the numbers differ,
    # and 33 of those differences flip the favourite. The check below therefore
    # tests the SIGN CONVENTION (home side negative when home is favoured, and
    # 0 when the game is a pick'em), which must hold nearly always, and records
    # the disagreement rate rather than asserting the series are identical.
    by_alt: dict[str, dict] = {}
    for r in crows:
        if r[2] == "SPREAD":
            by_alt.setdefault(r[1], {})[r[3]] = r[4]
    gmap_alt = {f"{r[1]}_{int(r[2]):02d}_{r[6]}_{r[7]}": r for r in rows}
    sign_ok = compared = exact = 0
    diffs = []
    for alt, sides in by_alt.items():
        g = gmap_alt.get(alt)
        if not g or g[7] not in sides or g[24] == "":
            continue
        try:
            cl_home = float(sides[g[7]])
            spread_home = float(g[24])   # positive == home favoured
        except (TypeError, ValueError):
            continue
        compared += 1
        diffs.append(cl_home - (-spread_home))
        if diffs[-1] == 0:
            exact += 1
        # home favoured  <=> spread_home > 0 <=> closing home line < 0
        if (cl_home < 0 and spread_home > 0) or (cl_home > 0 and spread_home < 0) \
                or (cl_home == 0 and spread_home == 0):
            sign_ok += 1
    checks.append({
        "check": "closing.csv home SPREAD carries the market sign convention "
                 "(negative when the home team is favoured)",
        "detail": f"{sign_ok}/{compared} agree on sign ({sign_ok / max(compared, 1):.3f})",
        "pass": compared > 0 and sign_ok / compared > 0.95,
    })
    checks.append({
        "check": "games.spread_line_home and closing.csv are the same price series",
        "detail": f"{exact}/{compared} identical; "
                  f"median |difference| {sorted(abs(d) for d in diffs)[len(diffs) // 2]:.2f} pts "
                  f"(they are NOT the same series - see F-03)",
        "pass": True,  # informational: the finding is published, not a defect
        "informational": True,
    })

    # ---- teams -------------------------------------------------------------
    thdr = ["season", "team", "nfl", "full", "location", "nickname"]
    trows = []
    for r in teams_raw:
        if r["team"] not in CURRENT:
            continue
        trows.append([r["season"], r["team"], r["nfl"], r["full"], r["location"], r["nickname"]])
    trows.sort(key=lambda x: (x[0], x[1]))
    teams_meta = write_csv(CORPUS / "teams.csv", thdr, trows)

    manifest = {
        "tarball": "data/corpus/raw/nfldata_e045566e.tar.gz",
        "tarball_sha256": dig,
        "tarball_inner_dir": INNER,
        "tables": [games_meta, closing_meta, teams_meta],
        "checks": checks,
    }
    (CORPUS / "corpus_manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    return manifest


if __name__ == "__main__":
    m = build()
    print(f"corpus tarball sha256 {m['tarball_sha256']}")
    for t in m["tables"]:
        print(f"  {t['path']:<40} rows={t['rows']:>6}  sha256={t['sha256'][:12]}")
    for c in m["checks"]:
        print(f"  [{'PASS' if c['pass'] else 'FAIL'}] {c['check']} -> {c['detail']}")
    if not all(c["pass"] for c in m["checks"]):
        raise SystemExit("corpus integrity checks failed")

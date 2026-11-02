"""Official-source verification of every backtest game.

The vendored nflverse game table is third-party. This module compares each
game's final score against the OFFICIAL NFL.com record and writes a per-game
ledger with the exact official URL used. Games that cannot be matched to an
official page are recorded as unverified and are excluded from graded results.

Official pages are retrieved by the agent (which has NFL.com access) and cached
as raw text under ``data/raw/official/``. This script parses that cache offline,
so the verification is reproducible without network access.

Two official page shapes are supported:
  1. Weekly scoreboard  https://www.nfl.com/scores/<season>/week-<n>
  2. Game Center        https://www.nfl.com/games/<away>-at-<home>-<season>-reg-<n>
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

from common import OUT, RAW, load_games, write_csv

CACHE = RAW / "official"

# NFL.com uses nickname slugs in URLs but abbreviations in the data table.
SLUG_TO_ABBR = {
    "cardinals": "ARI", "falcons": "ATL", "ravens": "BAL", "bills": "BUF",
    "panthers": "CAR", "bears": "CHI", "bengals": "CIN", "browns": "CLE",
    "cowboys": "DAL", "broncos": "DEN", "lions": "DET", "packers": "GB",
    "texans": "HOU", "colts": "IND", "jaguars": "JAX", "chiefs": "KC",
    "raiders": "LV", "chargers": "LAC", "rams": "LAR", "dolphins": "MIA",
    "vikings": "MIN", "patriots": "NE", "saints": "NO", "giants": "NYG",
    "jets": "NYJ", "eagles": "PHI", "steelers": "PIT", "seahawks": "SEA",
    "49ers": "SF", "buccaneers": "TB", "titans": "TEN", "commanders": "WAS",
}
# Franchise relocation aliases so older seasons still resolve.
ABBR_ALIAS = {"OAK": "LV", "SD": "LAC", "STL": "LAR", "WSH": "WAS"}


def norm_abbr(a: str) -> str:
    return ABBR_ALIAS.get(a, a)


def parse_scoreboard(text: str, season: int, week: int) -> list[dict]:
    """Parse an NFL.com weekly scoreboard text dump into game records.

    Each game block contains a "View <Away> <Home> game" link followed by two
    "<ABBR> ... <score> points" pairs. Scores rendered as "Hidden Score" are
    skipped, never guessed.
    """
    games: dict[str, dict] = {}
    # Split on the canonical game-center link, which names away and home slugs.
    pat = re.compile(
        r"https://www\.nfl\.com/games/([a-z0-9]+)-at-([a-z0-9]+)-(\d{4})-reg-(\d+)"
    )
    matches = list(pat.finditer(text))
    for i, m in enumerate(matches):
        away_slug, home_slug, yr, wk = m.groups()
        if int(yr) != season or int(wk) != week:
            continue
        away, home = SLUG_TO_ABBR.get(away_slug), SLUG_TO_ABBR.get(home_slug)
        if not away or not home:
            continue
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block = text[m.start():end]
        # Score tokens appear as "<ABBR><Name><ABBR><Name>\n\n<n>\n\n<n> points"
        scores = re.findall(r"\n\s*(\d{1,3})\s*\n\s*\1 points", block)
        rec = {
            "season": season, "week": week,
            "away_team": away, "home_team": home,
            "source_url": f"https://www.nfl.com/scores/{season}/week-{week}",
            "game_url": m.group(0),
        }
        if len(scores) >= 2 and "Hidden Score" not in block.split("points")[0]:
            rec["away_score"] = int(scores[0])
            rec["home_score"] = int(scores[1])
            rec["parse_status"] = "parsed"
        else:
            rec["away_score"] = None
            rec["home_score"] = None
            rec["parse_status"] = "score_hidden_or_unparsed"
        key = f"{season}_{week:02d}_{away}_{home}"
        # Prefer a parsed record over an unparsed duplicate.
        if key not in games or games[key]["parse_status"] != "parsed":
            games[key] = rec
    return list(games.values())


def parse_gamecenter(text: str, url: str) -> dict | None:
    """Parse a single official Game Center page (away listed first)."""
    m = re.search(r"/games/([a-z0-9]+)-at-([a-z0-9]+)-(\d{4})-reg-(\d+)", url)
    if not m:
        return None
    away_slug, home_slug, yr, wk = m.groups()
    away, home = SLUG_TO_ABBR.get(away_slug), SLUG_TO_ABBR.get(home_slug)
    if not away or not home:
        return None
    scores = re.findall(r"\n\s*(\d{1,3})\s*\n\s*\1 points", text[:6000])
    if len(scores) < 2:
        return None
    return {
        "season": int(yr), "week": int(wk),
        "away_team": away, "home_team": home,
        "away_score": int(scores[0]), "home_score": int(scores[1]),
        "source_url": url, "game_url": url, "parse_status": "parsed",
    }


def build_ledger() -> pd.DataFrame:
    """Parse every cached official page and compare to the vendored table."""
    CACHE.mkdir(parents=True, exist_ok=True)
    records: list[dict] = []
    for p in sorted(CACHE.glob("*.txt")):
        text = p.read_text(encoding="utf-8", errors="replace")
        meta_path = p.with_suffix(".json")
        meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
        url = meta.get("url", "")
        if meta.get("kind") == "gamecenter":
            rec = parse_gamecenter(text, url)
            if rec:
                records.append(rec)
        else:
            sm = re.search(r"/scores/(\d{4})/week-(\d+)", url) or re.search(
                r"(\d{4})[_-]week[_-](\d+)", p.name
            )
            if sm:
                records.extend(parse_scoreboard(text, int(sm.group(1)), int(sm.group(2))))

    if not records:
        return pd.DataFrame()

    off = pd.DataFrame(records)
    off = off[off["parse_status"] == "parsed"].copy()
    off["away_team"] = off["away_team"].map(norm_abbr)
    off["home_team"] = off["home_team"].map(norm_abbr)
    off = off.drop_duplicates(subset=["season", "week", "away_team", "home_team"], keep="first")

    g = load_games()
    g["home_team"] = g["home_team"].map(norm_abbr)
    g["away_team"] = g["away_team"].map(norm_abbr)

    merged = g.merge(
        off, on=["season", "week", "away_team", "home_team"],
        how="inner", suffixes=("", "_official"),
    )
    merged["score_match"] = (
        (merged["home_score"] == merged["home_score_official"])
        & (merged["away_score"] == merged["away_score_official"])
    )
    merged["verified"] = merged["score_match"]
    cols = [
        "game_id", "season", "week", "gameday", "away_team", "home_team",
        "away_score", "home_score", "away_score_official", "home_score_official",
        "score_match", "verified", "source_url", "game_url",
    ]
    return merged[cols].sort_values(["season", "week", "game_id"]).reset_index(drop=True)


def main() -> None:
    led = build_ledger()
    if led.empty:
        print("No cached official pages found. Nothing verified.")
        write_csv(pd.DataFrame(columns=[
            "game_id", "season", "week", "gameday", "away_team", "home_team",
            "away_score", "home_score", "away_score_official", "home_score_official",
            "score_match", "verified", "source_url", "game_url",
        ]), "official_verification.csv")
        return
    write_csv(led, "official_verification.csv")
    n = len(led)
    ok = int(led["verified"].sum())
    print(f"Official verification ledger: {n} games matched to an official page")
    print(f"  exact score match : {ok}/{n} ({ok / n:.2%})")
    print(f"  mismatches        : {n - ok}")
    if ok != n:
        bad = led[~led["verified"]]
        print(bad[["game_id", "away_score", "away_score_official",
                   "home_score", "home_score_official", "source_url"]].to_string(index=False))
    by_season = led.groupby("season").agg(games=("game_id", "size"), verified=("verified", "sum"))
    print("\nBy season:\n" + by_season.to_string())


if __name__ == "__main__":
    main()

"""Official-source verification of the vendored game table.

The nflverse game table is THIRD-PARTY. This module compares each game's final
score against a transcription of the OFFICIAL NFL.com scoreboard, row by row,
and writes a per-game ledger carrying the exact official URL.

Input : data/raw/official_transcribed.csv
        One row per game read from an official NFL.com weekly scoreboard:
        season, week, away_team, home_team, away_score, home_score, source_url.
        Values are transcribed from the rendered official page. Games whose
        score is rendered as "Hidden Score" are NOT transcribed and NOT guessed.

Output: data/empirical/official_verification.csv
        Joins each transcribed official row to the vendored table and records
        whether both scores match EXACTLY, plus the official source URL.

Anything not present in the official ledger stays unverified and is reported as
such. Unverified games are never silently promoted to verified.
"""
from __future__ import annotations

import pandas as pd

from common import OUT, RAW, load_games, write_csv, write_json

ABBR_ALIAS = {"OAK": "LV", "SD": "LAC", "STL": "LA", "WSH": "WAS", "LAR": "LA"}


def norm(a: str) -> str:
    return ABBR_ALIAS.get(str(a), str(a))


def build_ledger() -> pd.DataFrame:
    src = RAW / "official_transcribed.csv"
    if not src.exists():
        return pd.DataFrame()
    off = pd.read_csv(src)
    off = off.dropna(subset=["away_score", "home_score"]).copy()
    off["away_team"] = off["away_team"].map(norm)
    off["home_team"] = off["home_team"].map(norm)
    off["away_score"] = off["away_score"].astype(int)
    off["home_score"] = off["home_score"].astype(int)
    off = off.drop_duplicates(subset=["season", "week", "away_team", "home_team"], keep="first")
    off = off.rename(columns={"away_score": "away_score_official",
                              "home_score": "home_score_official"})

    g = load_games()
    g["away_team"] = g["away_team"].map(norm)
    g["home_team"] = g["home_team"].map(norm)

    m = g.merge(off, on=["season", "week", "away_team", "home_team"], how="inner")
    m["score_match"] = ((m.home_score == m.home_score_official)
                        & (m.away_score == m.away_score_official))
    m["verified"] = m["score_match"]
    m["game_url"] = m.apply(
        lambda r: f"https://www.nfl.com/games/{r.away_team.lower()}-at-{r.home_team.lower()}-{r.season}-reg-{r.week}",
        axis=1)
    cols = ["game_id", "season", "week", "gameday", "away_team", "home_team",
            "away_score", "home_score", "away_score_official", "home_score_official",
            "score_match", "verified", "source_url", "game_url"]
    led = m[cols].sort_values(["season", "week", "game_id"]).reset_index(drop=True)

    # Official rows that did not join are themselves an irregularity worth flagging.
    joined = set(zip(m.season, m.week, m.away_team, m.home_team))
    unmatched = off[~off.apply(lambda r: (r.season, r.week, r.away_team, r.home_team) in joined, axis=1)]
    if len(unmatched):
        write_csv(unmatched, "official_unmatched.csv")
    return led


def main() -> None:
    led = build_ledger()
    if led.empty:
        print("No official transcription ledger found; nothing verified.")
        return
    write_csv(led, "official_verification.csv")
    n, ok = len(led), int(led.verified.sum())
    print("=== OFFICIAL VERIFICATION (NFL.com) ===")
    print(f"  games compared : {n}")
    print(f"  exact matches  : {ok} ({ok/n:.2%})")
    print(f"  mismatches     : {n-ok}")
    if ok != n:
        print(led[~led.verified].to_string(index=False))
    bs = led.groupby("season").agg(games=("game_id", "size"), verified=("verified", "sum"))
    print("\nBy season:\n" + bs.to_string())

    g = load_games()
    total = len(g[(g.season >= 2006) & (g.season <= 2025)])
    write_json("verification_summary.json", {
        "official_games_compared": n,
        "exact_score_matches": ok,
        "mismatches": n - ok,
        "match_rate": round(ok / n, 6),
        "seasons_covered": sorted(int(s) for s in led.season.unique()),
        "backtest_universe_games": int(total),
        "verified_share_of_universe": round(n / total, 6),
        "official_source": "https://www.nfl.com/scores/",
        "status": ("all compared games match official scores" if ok == n
                   else "MISMATCHES PRESENT — see ledger"),
        "limitation": ("Official verification is a stratified sample of weeks, not a census. "
                       "Games outside the sample remain third-party-sourced and are labelled "
                       "unverified in every output table."),
    })


if __name__ == "__main__":
    main()

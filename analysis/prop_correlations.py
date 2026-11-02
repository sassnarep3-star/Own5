#!/usr/bin/env python3
"""Compute NBA player-prop correlation coefficients from OFFICIAL box-score data.

Purpose: fill the intentionally-blank `r` column of research/correlations.md
(table C1-C10) with values computed from official NBA statistics — never
inferred, never copied from unofficial aggregators.

Data source (run in an environment with network access to stats.nba.com):
    pip install nba_api pandas
    python analysis/prop_correlations.py --fetch --seasons 2024-25 2025-26

Or run against a local CSV export of official box scores:
    python analysis/prop_correlations.py --csv gamelogs.csv
    (required columns: PLAYER_ID, PLAYER_NAME, GAME_ID, PTS, REB, AST, FG3M,
     MIN, TEAM_PTS, WL)

Output: analysis/output/correlations.csv with per-player and league-wide
Pearson & Spearman r, sample sizes, and the season range — the provenance
fields required before any number may enter the published table.

NO SYNTHETIC OR PLACEHOLDER VALUES ARE EVER WRITTEN. If data is unavailable,
the script exits with an error instead of fabricating output.
"""
import argparse
import os
import sys

MIN_GAMES = 40  # minimum games per player for a per-player coefficient

PAIRS = [
    ("PTS", "AST", "C2: points vs assists (same player)"),
    ("PTS", "REB", "C3: points vs rebounds (same player)"),
    ("AST", "REB", "C4: assists vs rebounds (same player)"),
    ("FG3M", "PTS", "C5: threes made vs points (same player)"),
]


def fail(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    print("Refusing to emit placeholder values. Provide real official data.",
          file=sys.stderr)
    sys.exit(1)


def load_from_api(seasons):
    try:
        import pandas as pd
        from nba_api.stats.endpoints import playergamelogs
    except ImportError:
        fail("nba_api/pandas not installed. pip install nba_api pandas")
    frames = []
    for season in seasons:
        logs = playergamelogs.PlayerGameLogs(season_nullable=season)
        df = logs.get_data_frames()[0]
        df["SEASON"] = season
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def load_from_csv(path):
    import pandas as pd
    if not os.path.exists(path):
        fail(f"CSV not found: {path}")
    return pd.read_csv(path)


def compute(df, out_path):
    import pandas as pd
    from scipy.stats import pearsonr, spearmanr

    needed = {"PLAYER_ID", "PTS", "REB", "AST", "FG3M"}
    missing = needed - set(df.columns)
    if missing:
        fail(f"input missing required columns: {sorted(missing)}")

    rows = []
    # League-wide (pooled game-level) coefficients
    for a, b, label in PAIRS:
        sub = df[[a, b]].dropna()
        if len(sub) < 100:
            fail(f"insufficient rows for league-wide {label}: {len(sub)}")
        pr, pp = pearsonr(sub[a], sub[b])
        sr, sp = spearmanr(sub[a], sub[b])
        rows.append({"scope": "league", "player": "", "pair": label,
                     "pearson_r": round(pr, 4), "pearson_p": pp,
                     "spearman_r": round(sr, 4), "spearman_p": sp,
                     "n_games": len(sub)})
    # Per-player coefficients (players with >= MIN_GAMES)
    for pid, g in df.groupby("PLAYER_ID"):
        if len(g) < MIN_GAMES:
            continue
        name = g["PLAYER_NAME"].iloc[0] if "PLAYER_NAME" in g else str(pid)
        for a, b, label in PAIRS:
            sub = g[[a, b]].dropna()
            if len(sub) < MIN_GAMES:
                continue
            pr, pp = pearsonr(sub[a], sub[b])
            sr, sp = spearmanr(sub[a], sub[b])
            rows.append({"scope": "player", "player": name, "pair": label,
                         "pearson_r": round(pr, 4), "pearson_p": pp,
                         "spearman_r": round(sr, 4), "spearman_p": sp,
                         "n_games": len(sub)})
    out = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    out.to_csv(out_path, index=False)
    print(f"Wrote {len(out)} coefficient rows -> {out_path}")
    print("Attach season range + official source link before publishing.")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fetch", action="store_true",
                    help="fetch from stats.nba.com via nba_api")
    ap.add_argument("--seasons", nargs="*", default=["2024-25", "2025-26"])
    ap.add_argument("--csv", help="local CSV of official box scores")
    ap.add_argument("--out", default="analysis/output/correlations.csv")
    args = ap.parse_args()

    if args.csv:
        df = load_from_csv(args.csv)
    elif args.fetch:
        df = load_from_api(args.seasons)
    else:
        fail("choose --fetch (needs stats.nba.com access) or --csv PATH")
    compute(df, args.out)


if __name__ == "__main__":
    main()

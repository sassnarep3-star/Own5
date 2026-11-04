"""Load the verified NBA 2026-27 CSV tables into plain Python structures."""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "nba-2026-27"

INT_COLS_STATS = {"gp", "w", "l"}
FLOAT_COLS_STATS = {
    "win_pct", "min", "pts", "fgm", "fga", "fg_pct", "fg3m", "fg3a", "fg3_pct",
    "ftm", "fta", "ft_pct", "oreb", "dreb", "reb", "ast", "tov", "stl", "blk",
    "blka", "pf", "pfd", "plus_minus",
}


def _read(name):
    with open(DATA / name, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _num(v):
    v = v.strip()
    if v == "":
        return None
    try:
        return float(v)
    except ValueError:
        return v


def load_standings():
    rows = _read("standings.csv")
    for r in rows:
        r["w"] = int(r["w"])
        r["l"] = int(r["l"])
        r["conf_rank"] = int(r["conf_rank"])
        r["pct"] = float(r["pct"])
    return rows


def load_team_stats():
    rows = _read("team_stats_traditional.csv")
    out = []
    for r in rows:
        rr = {}
        for k, v in r.items():
            if k in INT_COLS_STATS:
                rr[k] = int(v)
            elif k in FLOAT_COLS_STATS:
                rr[k] = float(v)
            else:
                rr[k] = v
        out.append(rr)
    return out


def load_prior_standings():
    rows = _read("prior_standings_2025-26.csv")
    for r in rows:
        r["w"] = int(r["w"])
        r["l"] = int(r["l"])
        r["pct"] = float(r["pct"])
    return rows


def load_player_logs():
    rows = _read("player_logs_edwards.csv")
    int_cols = [
        "min", "pts", "fgm", "fga", "fg3m", "fg3a", "ftm", "fta", "oreb", "dreb",
        "reb", "ast", "stl", "blk", "tov", "pf", "plus_minus",
    ]
    for r in rows:
        for c in int_cols:
            r[c] = int(r[c])
    return rows


def load_sources():
    return {r["source_id"]: r for r in _read("sources.csv")}


def load_flags():
    return _read("flags.csv")


def load_strategies():
    return _read("strategies.csv")


def load_signals():
    return _read("signals.csv")


def load_gates():
    return _read("gates.csv")

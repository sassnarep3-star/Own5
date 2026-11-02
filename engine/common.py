"""Shared data layer for the OWN5 empirical engine.

Provenance
----------
Raw inputs are vendored under ``data/raw/`` from the nflverse ``nfldata`` project
(pinned commit recorded in ``data/raw/PROVENANCE.json``). nflverse is a third-party
open-data project, NOT an official NFL source. Every game used in a backtest is
therefore cross-checked against official NFL.com box scores by
``engine/verify_official.py``; only games whose final score matches the official
record are marked ``official_verified`` and allowed into graded results.

Sign conventions (verified against upstream DATASETS.md, see provenance file):
  result       = home_score - away_score
  spread_line  > 0 means the HOME team is favored by that many points.
               Home covers when (result - spread_line) > 0.
  total_line   = the posted game total; over wins when (total - total_line) > 0.
American odds are converted to decimal and de-vigged proportionally.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "empirical"

# Regular-season games only. Playoff markets are structurally different
# (motivation, roster usage, no tomorrow) and are excluded from the core book.
MIN_SEASON = 2006
MAX_SEASON = 2025


def american_to_decimal(odds: pd.Series | np.ndarray | float) -> np.ndarray:
    """American odds -> decimal odds (total return per 1 unit staked)."""
    o = np.asarray(odds, dtype=float)
    return np.where(o > 0, 1.0 + o / 100.0, 1.0 + 100.0 / np.abs(o))


def american_to_prob(odds: pd.Series | np.ndarray | float) -> np.ndarray:
    """American odds -> raw implied probability (still contains the vig).

    Both branches are evaluated by np.where, so denominators are guarded to
    avoid spurious divide-by-zero warnings on exactly -100 prices.
    """
    o = np.asarray(odds, dtype=float)
    pos_den = np.where(o > 0, o + 100.0, 1.0)
    neg_abs = np.abs(np.where(o > 0, 1.0, o))
    return np.where(o > 0, 100.0 / pos_den, neg_abs / (neg_abs + 100.0))


def devig_two_way(p_a: np.ndarray, p_b: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Proportional (multiplicative) de-vig of a two-way market.

    Returns fair probabilities summing to 1. This is the standard baseline;
    it is known to be mildly biased toward the longshot relative to Shin or
    power methods, which is documented as a limitation rather than hidden.
    """
    s = p_a + p_b
    return p_a / s, p_b / s


# Upstream uses legacy/odd franchise codes. Normalise to current official codes
# so that joins to official NFL.com records and to player tables are consistent.
TEAM_ALIAS = {"OAK": "LV", "SD": "LAC", "STL": "LA", "WSH": "WAS", "LAR": "LA"}


def load_games() -> pd.DataFrame:
    """Load, clean and derive the regular-season game table."""
    g = pd.read_csv(RAW / "games.csv")
    g["home_team"] = g["home_team"].replace(TEAM_ALIAS)
    g["away_team"] = g["away_team"].replace(TEAM_ALIAS)
    g = g[g["game_type"] == "REG"].copy()
    g = g[(g["season"] >= MIN_SEASON) & (g["season"] <= MAX_SEASON)].copy()
    g = g[g["home_score"].notna() & g["away_score"].notna()].copy()

    g["home_score"] = g["home_score"].astype(int)
    g["away_score"] = g["away_score"].astype(int)
    g["result"] = g["home_score"] - g["away_score"]
    g["total"] = g["home_score"] + g["away_score"]
    g["gameday"] = pd.to_datetime(g["gameday"])
    g = g.sort_values(["gameday", "game_id"]).reset_index(drop=True)

    # Rest / scheduling features. away_rest and home_rest are upstream fields.
    g["rest_diff"] = g["home_rest"] - g["away_rest"]
    g["home_bye"] = (g["home_rest"] > 10).astype(int)
    g["away_bye"] = (g["away_rest"] > 10).astype(int)
    g["short_week_home"] = (g["home_rest"] <= 6).astype(int)
    g["short_week_away"] = (g["away_rest"] <= 6).astype(int)
    g["div_game"] = g["div_game"].fillna(0).astype(int)
    g["is_neutral"] = (g["location"] == "Neutral").astype(int)

    # Market prices. Missing odds fall back to the standard -110 assumption,
    # and that assumption is recorded per row so it is never silently applied.
    g["spread_odds_home"] = g["home_spread_odds"]
    g["spread_odds_away"] = g["away_spread_odds"]
    g["spread_odds_assumed"] = (
        g["spread_odds_home"].isna() | g["spread_odds_away"].isna()
    ).astype(int)
    g["spread_odds_home"] = g["spread_odds_home"].fillna(-110.0)
    g["spread_odds_away"] = g["spread_odds_away"].fillna(-110.0)

    g["total_odds_over"] = g["over_odds"].fillna(-110.0)
    g["total_odds_under"] = g["under_odds"].fillna(-110.0)
    g["total_odds_assumed"] = (g["over_odds"].isna() | g["under_odds"].isna()).astype(int)

    # De-vigged market probabilities for the spread market.
    ph = american_to_prob(g["spread_odds_home"].values)
    pa = american_to_prob(g["spread_odds_away"].values)
    g["mkt_p_home_cover"], g["mkt_p_away_cover"] = devig_two_way(ph, pa)

    po = american_to_prob(g["total_odds_over"].values)
    pu = american_to_prob(g["total_odds_under"].values)
    g["mkt_p_over"], g["mkt_p_under"] = devig_two_way(po, pu)

    # Moneyline (available from 2006 onward for most games).
    hm = american_to_prob(g["home_moneyline"].fillna(0).replace(0, np.nan).values)
    am = american_to_prob(g["away_moneyline"].fillna(0).replace(0, np.nan).values)
    with np.errstate(invalid="ignore"):
        fh, fa = devig_two_way(hm, am)
    g["mkt_p_home_win"] = fh
    g["mkt_p_away_win"] = fa

    # Settlement outcomes (push = 0). Home spread = -spread_line in book notation.
    g["home_cover_margin"] = g["result"] - g["spread_line"]
    g["total_margin"] = g["total"] - g["total_line"]
    return g


def attach_verification(g: pd.DataFrame) -> pd.DataFrame:
    """Join the official-source verification ledger onto the game table.

    A game is ``official_verified`` only when engine/verify_official.py recorded
    an exact home/away score match against an official NFL.com page.
    """
    path = OUT / "official_verification.csv"
    if not path.exists():
        g["official_verified"] = False
        g["official_source_url"] = ""
        return g
    v = pd.read_csv(path)
    v = v[["game_id", "verified", "source_url"]].rename(
        columns={"verified": "official_verified", "source_url": "official_source_url"}
    )
    g = g.merge(v, on="game_id", how="left")
    g["official_verified"] = g["official_verified"].fillna(False).astype(bool)
    g["official_source_url"] = g["official_source_url"].fillna("")
    return g


def settled(mask_push: np.ndarray) -> np.ndarray:
    """Map a signed margin to +1 win / -1 loss / 0 push."""
    m = np.asarray(mask_push, dtype=float)
    return np.sign(m)


def write_json(name: str, obj) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / name
    p.write_text(json.dumps(obj, indent=2, default=str) + "\n", encoding="utf-8")
    return p


def write_csv(df: pd.DataFrame, name: str) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / name
    df.to_csv(p, index=False)
    return p

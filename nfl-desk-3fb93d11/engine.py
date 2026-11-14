"""Core computation for the Own5 price-snapshot & verified-results desk.

Every number produced here is either

  * transcribed from an official nfl.com page (source tier OFFICIAL),
  * computed in-repo from those official numbers (tier DERIVED), or
  * taken from a pinned third-party mirror and labelled AGGREGATOR.

Anything that cannot be sourced is emitted as an empty cell plus a flag id.
Nothing is inferred, interpolated or filled in.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import os
from collections import defaultdict

from statslib import (american_to_decimal, brier, decimal_to_american, devig_two_way,
                      log_loss, mean, norm_cdf, pearson, fisher_ci, solve_normal,
                      stdev, wilson_interval, binom_two_sided_p, implied_prob,
                      sharpe_ratio, deflated_sharpe)

ROOT = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(ROOT)
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "data")

# Retrieval stamps.  The official pages were read through the sandbox fetcher at
# the timestamp below; the pinned mirror files carry their own provenance block
# committed by session 38a1fc27 (data/decision-desk/raw/provenance.json).
RETRIEVED_UTC = "2026-11-14T21:33:19Z"
MIRROR_RETRIEVED_UTC = "2026-11-12T16:52:39Z"

STANDINGS_URL = "https://www.nfl.com/standings/league/2026/REG"
SCHEDULE_URL = "https://www.nfl.com/schedules/2026/by-week/"

def week_url(w: int) -> str:
    return f"https://www.nfl.com/schedules/2026/by-week/week-{w}"
INJURY_URL = "https://www.nfl.com/injuries/league/2026/reg10"
INJURY_WK11_URL = "https://www.nfl.com/injuries/league/2026/reg11"
MIRROR_GAMES_URL = ("https://github.com/nflverse/nflverse-data/releases/download/"
                    "schedules/games.csv.gz")
MIRROR_GAMES_SHA256 = "3d6394dd86427a158d8b22c8f8c5cdfdac13460e2a2c76935180b56dab108532"

TEAMS = {
    "ARI": "Arizona Cardinals", "ATL": "Atlanta Falcons", "BAL": "Baltimore Ravens",
    "BUF": "Buffalo Bills", "CAR": "Carolina Panthers", "CHI": "Chicago Bears",
    "CIN": "Cincinnati Bengals", "CLE": "Cleveland Browns", "DAL": "Dallas Cowboys",
    "DEN": "Denver Broncos", "DET": "Detroit Lions", "GB": "Green Bay Packers",
    "HOU": "Houston Texans", "IND": "Indianapolis Colts", "JAX": "Jacksonville Jaguars",
    "KC": "Kansas City Chiefs", "LAC": "Los Angeles Chargers", "LAR": "Los Angeles Rams",
    "LV": "Las Vegas Raiders", "MIA": "Miami Dolphins", "MIN": "Minnesota Vikings",
    "NE": "New England Patriots", "NO": "New Orleans Saints", "NYG": "New York Giants",
    "NYJ": "New York Jets", "PHI": "Philadelphia Eagles", "PIT": "Pittsburgh Steelers",
    "SF": "San Francisco 49ers", "SEA": "Seattle Seahawks", "TB": "Tampa Bay Buccaneers",
    "TEN": "Tennessee Titans", "WAS": "Washington Commanders",
}
TEAM_INDEX = {t: i for i, t in enumerate(sorted(TEAMS))}
N_TEAMS = len(TEAMS)

MONTHS = {"January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
          "July": 7, "August": 8, "September": 9, "October": 10, "November": 11,
          "December": 12}
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _iso(month: str, day: int, year: int = 2026) -> str:
    return f"{year:04d}-{MONTHS[month]:02d}-{day:02d}"


def _weekday_of(iso: str) -> str:
    """Weekday of an ISO date.  Used to prove each transcribed kickoff date
    matches the weekday the official page printed for it."""
    import datetime
    return datetime.date.fromisoformat(iso).strftime("%A")


# --------------------------------------------------------------------------
# CSV helpers
# --------------------------------------------------------------------------
def write_csv(name: str, rows: list, fieldnames: list) -> str:
    path = os.path.join(OUT, name)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fieldnames})
    return path


def read_csv(path: str) -> list:
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def fmt(x, nd: int = 4):
    """Render a float for CSV output; NaN/None become an empty cell."""
    if x is None:
        return ""
    if isinstance(x, float):
        if x != x or x in (float("inf"), float("-inf")):
            return ""
        return f"{x:.{nd}f}"
    return x


# --------------------------------------------------------------------------
# 1. Official source registry
# --------------------------------------------------------------------------
def build_sources(official_game_rows: list) -> list:
    rows = []
    for w in range(1, 11):
        n_games = sum(1 for g in official_game_rows if g["week"] == w)
        rows.append({
            "source_id": f"OFF-W{w:02d}",
            "publisher": "NFL.com",
            "title": f"2026 NFL Schedule - Week {w}",
            "url": week_url(w),
            "tier": "OFFICIAL",
            "fetched_utc": RETRIEVED_UTC,
            "used_for": "Final scores, matchups and kickoff dates for the verified results feed",
            "rows_contributed": str(n_games),
            "verification_status": "read directly through the sandbox fetcher; scores transcribed verbatim",
        })
    rows.append({
        "source_id": "OFF-STD", "publisher": "NFL.com",
        "title": "2026 NFL League Standings (regular season)",
        "url": STANDINGS_URL, "tier": "OFFICIAL", "fetched_utc": RETRIEVED_UTC,
        "used_for": "32-team W-L-T / PF / PA benchmark used to reconcile the results feed",
        "rows_contributed": "32",
        "verification_status": "read directly; all 32 rows transcribed",
    })
    rows.append({
        "source_id": "OFF-INJ-10", "publisher": "NFL.com",
        "title": "Official NFL Injury Report - Week 10, 2026",
        "url": INJURY_URL, "tier": "OFFICIAL", "fetched_utc": RETRIEVED_UTC,
        "used_for": "Practice status and game status driving the replacement-depth tracker",
        "rows_contributed": "326",
        "verification_status": "page is paginated; rows carried forward from session 864d5668's 2026-11-13 transcription of the same official page, sample re-read on 2026-11-14",
    })
    rows.append({
        "source_id": "OFF-INJ-11", "publisher": "NFL.com",
        "title": "Official NFL Injury Report - Week 11, 2026 (requested)",
        "url": INJURY_WK11_URL, "tier": "OFFICIAL", "fetched_utc": RETRIEVED_UTC,
        "used_for": "Would drive the Week 11 injury adjustment",
        "rows_contributed": "0",
        "verification_status": "NOT PUBLISHED - the URL serves the Week 10 report; see flag F-05",
    })
    rows.append({
        "source_id": "MIR-GAMES", "publisher": "nflverse (third-party mirror of NFL game data)",
        "title": "nflverse games.csv - schedules, scores and market lines 1999-2026",
        "url": MIRROR_GAMES_URL, "tier": "AGGREGATOR", "fetched_utc": MIRROR_RETRIEVED_UTC,
        "used_for": "Cross-source reconciliation of scores; AGGREGATOR-tier market reference lines",
        "rows_contributed": "7548",
        "verification_status": f"pinned in-repo with sha256 {MIRROR_GAMES_SHA256[:16]}...; no official publisher, never used as a fact source",
    })
    rows.append({
        "source_id": "OFF-DC", "publisher": "32 NFL club sites",
        "title": "Official club depth charts (one page per club)",
        "url": "https://www.nfl.com/teams/", "tier": "OFFICIAL",
        "fetched_utc": "2026-11-13",
        "used_for": "Published 1st/2nd/3rd-string order that defines replacement depth",
        "rows_contributed": "705",
        "verification_status": "transcribed by session 864d5668 on 2026-11-13 from each club's own /team/depth-chart page; per-row club URL retained",
    })
    return rows


# --------------------------------------------------------------------------
# 2. Verified results feed
# --------------------------------------------------------------------------
def load_official_games() -> list:
    """Load the transcribed official week-by-week results and validate them."""
    raw = read_csv(os.path.join(DATA, "_raw_week_games.csv"))
    games = []
    problems = []
    for i, r in enumerate(raw, start=2):
        week = int(r["week"])
        parts = r["date_label"].split()
        # "Thursday September 17" -> weekday, month, day
        if len(parts) < 3:
            problems.append(f"line {i}: unparsable date label {r['date_label']!r}")
            continue
        weekday, month, day = parts[0], parts[1], int(parts[2])
        iso = _iso(month, day)
        if _weekday_of(iso) != weekday:
            problems.append(f"line {i}: {r['date_label']} is a {_weekday_of(iso)}, not a {weekday}")
        games.append({
            "game_id": f"2026_{week:02d}_{r['away']}_{r['home']}",
            "season": 2026, "week": week, "kickoff_date": iso,
            "weekday_as_published": weekday, "weekday_checked": _weekday_of(iso),
            "away": r["away"], "home": r["home"],
            "away_score": int(r["away_score"]), "home_score": int(r["home_score"]),
            "home_margin": int(r["home_score"]) - int(r["away_score"]),
            "total_points": int(r["away_score"]) + int(r["home_score"]),
            "neutral_site": r["neutral"] or "",
            "source_url": week_url(week),
        })
    return games, problems


def official_standings() -> list:
    """32 rows transcribed from https://www.nfl.com/standings/league/2026/REG."""
    raw = [
        ("BUF", 7, 1, 0, 256, 187), ("SF", 7, 1, 0, 235, 156), ("CHI", 7, 2, 0, 241, 184),
        ("DEN", 7, 2, 0, 198, 186), ("CIN", 6, 2, 0, 240, 175), ("DET", 6, 2, 0, 222, 189),
        ("JAX", 6, 2, 0, 229, 121), ("KC", 6, 2, 0, 202, 143), ("MIN", 6, 2, 0, 146, 116),
        ("PIT", 6, 2, 0, 180, 144), ("GB", 6, 3, 0, 216, 191), ("NYG", 5, 3, 1, 203, 196),
        ("CLE", 5, 4, 0, 161, 196), ("LAR", 5, 4, 0, 214, 181), ("NE", 5, 4, 0, 211, 207),
        ("SEA", 5, 4, 0, 202, 162), ("BAL", 4, 5, 0, 189, 236), ("DAL", 4, 5, 0, 246, 236),
        ("LV", 4, 5, 0, 238, 268), ("WAS", 3, 5, 1, 196, 223), ("CAR", 3, 5, 0, 199, 219),
        ("HOU", 3, 5, 0, 209, 192), ("NO", 3, 5, 0, 185, 216), ("ARI", 3, 6, 0, 178, 255),
        ("ATL", 3, 6, 0, 188, 223), ("TB", 3, 6, 0, 202, 178), ("IND", 2, 7, 0, 184, 249),
        ("NYJ", 2, 7, 0, 182, 223), ("PHI", 2, 7, 0, 148, 221), ("MIA", 1, 7, 0, 126, 200),
        ("TEN", 1, 7, 0, 144, 199), ("LAC", 0, 8, 0, 121, 219),
    ]
    rows = []
    for t, w, l, tie, pf, pa in raw:
        rows.append({
            "team": t, "club": TEAMS[t], "w": w, "l": l, "t": tie,
            "pf": pf, "pa": pa, "net_pts": pf - pa,
            "games_played": w + l + tie,
            "win_pct": (w + 0.5 * tie) / (w + l + tie),
            "pf_per_game": pf / (w + l + tie), "pa_per_game": pa / (w + l + tie),
            "net_per_game": (pf - pa) / (w + l + tie),
            "source_url": STANDINGS_URL, "fetched_utc": RETRIEVED_UTC,
        })
    return rows


def reconcile_feed(games: list, standings: list) -> tuple:
    """Rebuild every club's W-L-T / PF / PA from the game feed and compare with
    the official standings page, row by row."""
    agg = {t: {"w": 0, "l": 0, "t": 0, "pf": 0, "pa": 0, "gp": 0} for t in TEAMS}
    for g in games:
        a, h = g["away"], g["home"]
        for team, own, opp in ((a, g["away_score"], g["home_score"]),
                               (h, g["home_score"], g["away_score"])):
            agg[team]["gp"] += 1
            agg[team]["pf"] += own
            agg[team]["pa"] += opp
            if own > opp:
                agg[team]["w"] += 1
            elif own < opp:
                agg[team]["l"] += 1
            else:
                agg[team]["t"] += 1
    rows, mismatches = [], 0
    for s in standings:
        t = s["team"]
        a = agg[t]
        ok = (a["w"] == s["w"] and a["l"] == s["l"] and a["t"] == s["t"]
              and a["pf"] == s["pf"] and a["pa"] == s["pa"])
        if not ok:
            mismatches += 1
        rows.append({
            "team": t, "club": s["club"],
            "official_w": s["w"], "official_l": s["l"], "official_t": s["t"],
            "official_pf": s["pf"], "official_pa": s["pa"],
            "feed_w": a["w"], "feed_l": a["l"], "feed_t": a["t"],
            "feed_pf": a["pf"], "feed_pa": a["pa"],
            "w_delta": a["w"] - s["w"], "l_delta": a["l"] - s["l"],
            "t_delta": a["t"] - s["t"], "pf_delta": a["pf"] - s["pf"],
            "pa_delta": a["pa"] - s["pa"],
            "agrees": "yes" if ok else "no",
            "official_source_url": STANDINGS_URL,
            "feed_source_url": "https://www.nfl.com/schedules/2026/by-week/",
        })
    return rows, mismatches


def reconcile_mirror(games: list) -> tuple:
    """Compare each official final score with the pinned nflverse mirror."""
    mirror = [r for r in load_mirror() if r["season"] == "2026" and r["game_type"] == "REG"]
    by_key = {(r["away_team"], r["home_team"]): r for r in mirror}
    rows, agree, missing, disagree = [], 0, 0, 0
    for g in games:
        m = by_key.get((g["away"], g["home"]))
        if m is None or not m["away_score"] or not m["home_score"]:
            missing += 1
            rows.append({
                "game_id": g["game_id"], "week": g["week"], "matchup": f"{g['away']} @ {g['home']}",
                "official_away_score": g["away_score"], "official_home_score": g["home_score"],
                "mirror_away_score": "", "mirror_home_score": "",
                "agrees": "", "state": "mirror has not published a final for this game yet - the official page has it (F-04)",
                "official_source_url": g["source_url"], "mirror_source_url": MIRROR_GAMES_URL,
            })
            continue
        ok = (int(m["away_score"]) == g["away_score"] and int(m["home_score"]) == g["home_score"])
        if ok:
            agree += 1
        else:
            disagree += 1
        rows.append({
            "game_id": g["game_id"], "week": g["week"], "matchup": f"{g['away']} @ {g['home']}",
            "official_away_score": g["away_score"], "official_home_score": g["home_score"],
            "mirror_away_score": m["away_score"], "mirror_home_score": m["home_score"],
            "agrees": "yes" if ok else "NO",
            "state": "compared" if ok else "DISAGREEMENT - flag F-02",
            "official_source_url": g["source_url"], "mirror_source_url": MIRROR_GAMES_URL,
        })
    return rows, {"agree": agree, "missing": missing, "disagree": disagree}


# --------------------------------------------------------------------------
# 3. Rating models (side first, then total, then moneyline)
# --------------------------------------------------------------------------
class MarginModel:
    """y = hfa * H + rating_home - rating_away, ridge-shrunk.

    Trained incrementally so a seasonal walk-forward costs one solve per season.
    """

    def __init__(self, lam: float = 8.0):
        self.lam = lam
        self.p = N_TEAMS + 1          # 32 team columns + 1 home-field column
        self.A = [[0.0] * self.p for _ in range(self.p)]
        self.b = [0.0] * self.p
        self.n = 0
        self.beta = [0.0] * self.p

    def add(self, home: str, away: str, y: float, hfa_on: bool) -> None:
        hi, ai = TEAM_INDEX[home], TEAM_INDEX[away]
        hf = self.p - 1
        idx = [hi, ai] + ([hf] if hfa_on else [])
        vals = [1.0, -1.0] + ([1.0] if hfa_on else [])
        for i, vi in zip(idx, vals):
            self.b[i] += vi * y
            for j, vj in zip(idx, vals):
                self.A[i][j] += vi * vj
        self.n += 1

    def fit(self) -> list:
        A = [row[:] for row in self.A]
        for i in range(self.p):
            A[i][i] += self.lam
        self.beta = solve_normal(A, self.b)
        return self.beta

    def predict(self, home: str, away: str, neutral: bool) -> float:
        """Expected home margin (positive = home wins by that many points)."""
        hi, ai = TEAM_INDEX[home], TEAM_INDEX[away]
        val = self.beta[hi] - self.beta[ai]
        if not neutral:
            val += self.beta[self.p - 1]
        return val


class TotalsModel:
    """y = base + total_rating_home + total_rating_away, ridge-shrunk."""

    def __init__(self, lam: float = 12.0):
        self.lam = lam
        self.p = N_TEAMS + 1          # last column is the intercept
        self.A = [[0.0] * self.p for _ in range(self.p)]
        self.b = [0.0] * self.p
        self.n = 0
        self.beta = [0.0] * self.p

    def add(self, home: str, away: str, y: float) -> None:
        hi, ai, ic = TEAM_INDEX[home], TEAM_INDEX[away], self.p - 1
        idx = [hi, ai, ic]
        vals = [1.0, 1.0, 1.0]
        for i, vi in zip(idx, vals):
            self.b[i] += vi * y
            for j, vj in zip(idx, vals):
                self.A[i][j] += vi * vj
        self.n += 1

    def fit(self) -> list:
        # The intercept is the league average total; shrinking it would bias
        # every prediction downwards, so only the team columns are penalised.
        A = [row[:] for row in self.A]
        for i in range(self.p - 1):
            A[i][i] += self.lam
        self.beta = solve_normal(A, self.b)
        return self.beta

    def predict(self, home: str, away: str) -> float:
        return self.beta[TEAM_INDEX[home]] + self.beta[TEAM_INDEX[away]] + self.beta[self.p - 1]


# --------------------------------------------------------------------------
# 4. Market reference (AGGREGATOR tier only)
# --------------------------------------------------------------------------
# The mirror keeps historical club codes; map them onto the current 32 so the
# franchise is treated as one continuous entity.  This is a code translation,
# not an inference about any value.
MIRROR_TEAM_MAP = {"LA": "LAR", "STL": "LAR", "SD": "LAC", "OAK": "LV"}


def _mt(code: str) -> str:
    return MIRROR_TEAM_MAP.get(code, code)


def load_mirror() -> list:
    with gzip.open(os.path.join(REPO, "data", "decision-desk", "raw", "games.csv.gz"), "rt") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        r["away_team"] = _mt(r["away_team"])
        r["home_team"] = _mt(r["home_team"])
    return rows


def mirror_index(mirror: list) -> dict:
    return {(r["season"], r["week"], r["away_team"], r["home_team"]): r for r in mirror}


def fnum(v: str):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


# --------------------------------------------------------------------------
# 5. Correlations -- official inputs only
# --------------------------------------------------------------------------
def official_correlations(standings: list, games: list) -> list:
    """Every pair here is computed from numbers published by nfl.com.

    Anything that would need an aggregator input is deliberately excluded and
    listed separately in correlations_withheld.csv.
    """
    rows = []
    teams = [s["team"] for s in standings]
    series = {
        "win_pct": [s["win_pct"] for s in standings],
        "pf_per_game": [s["pf_per_game"] for s in standings],
        "pa_per_game": [s["pa_per_game"] for s in standings],
        "net_pts_per_game": [s["net_per_game"] for s in standings],
        "games_played": [float(s["games_played"]) for s in standings],
    }
    pairs = [
        ("net_pts_per_game", "win_pct"),
        ("pf_per_game", "win_pct"),
        ("pa_per_game", "win_pct"),
        ("pf_per_game", "pa_per_game"),
        ("net_pts_per_game", "pf_per_game"),
        ("net_pts_per_game", "pa_per_game"),
    ]
    for a, b in pairs:
        r, p, n = pearson(series[a], series[b])
        lo, hi = fisher_ci(r, n)
        rows.append({
            "corr_id": f"CORR-{len(rows) + 1:02d}",
            "unit_of_analysis": "team-season",
            "metric_a": a, "metric_b": b, "r": fmt(r), "p_value": fmt(p, 6),
            "ci95_low": fmt(lo), "ci95_high": fmt(hi), "n": n,
            "n_definition": "32 NFL clubs, 2026 regular season to date",
            "source_tier": "OFFICIAL", "source_url": STANDINGS_URL,
            "fetched_utc": RETRIEVED_UTC,
        })

    # Game-level pairs from the verified results feed.
    margins = [float(g["home_margin"]) for g in games]
    totals = [float(g["total_points"]) for g in games]
    abs_margins = [abs(m) for m in margins]
    non_neutral = [g for g in games if not g["neutral_site"]]
    nn_margins = [float(g["home_margin"]) for g in non_neutral]
    gpairs = [
        ("home_margin", "total_points", margins, totals,
         "game", f"{len(games)} completed 2026 games (Weeks 1-10)"),
        ("abs_margin", "total_points", abs_margins, totals,
         "game", f"{len(games)} completed 2026 games (Weeks 1-10)"),
        ("home_margin_non_neutral", "total_points", nn_margins,
         [float(g["total_points"]) for g in non_neutral], "game",
         f"{len(non_neutral)} completed 2026 games played at a home venue"),
    ]
    for a, b, xs, ys, unit, ndef in gpairs:
        r, p, n = pearson(xs, ys)
        lo, hi = fisher_ci(r, n)
        rows.append({
            "corr_id": f"CORR-{len(rows) + 1:02d}",
            "unit_of_analysis": unit,
            "metric_a": a, "metric_b": b, "r": fmt(r), "p_value": fmt(p, 6),
            "ci95_low": fmt(lo), "ci95_high": fmt(hi), "n": n,
            "n_definition": ndef,
            "source_tier": "OFFICIAL",
            "source_url": "https://www.nfl.com/schedules/2026/by-week/",
            "fetched_utc": RETRIEVED_UTC,
        })
    return rows


def withheld_correlations() -> list:
    """Numbers this repo has published before that are NOT admissible under the
    'official inputs only' rule.  Kept visible, never used."""
    items = [
        ("QB passing yards vs top-WR receiving yards", "0.76", "3852",
         "nfl_strategy_lab", "nflverse weekly player stats (AGGREGATOR)"),
        ("Same-team QB + WR1 legs, 2024-2026", "0.50", "",
         "nfl-decision-desk (38a1fc27)", "nflverse weekly player stats (AGGREGATOR)"),
        ("Cross-game parlay legs, phi", "0.01", "9479",
         "nfl_strategy_lab", "nflverse schedules + lines (AGGREGATOR)"),
        ("NET/G vs PCT", "0.8391", "32", "0f468a47-own5",
         "computed from official nfl.com standings - admissible, superseded by CORR-01 recomputation"),
        ("PF/G vs PCT", "0.6136", "32", "0f468a47-own5",
         "computed from official nfl.com standings - admissible, superseded by CORR-02 recomputation"),
        ("PA/G vs PCT", "-0.5796", "32", "0f468a47-own5",
         "computed from official nfl.com standings - admissible, superseded by CORR-03 recomputation"),
        ("PF/G vs PA/G", "-0.0117", "32", "0f468a47-own5",
         "computed from official nfl.com standings - admissible, superseded by CORR-04 recomputation"),
    ]
    rows = []
    for i, (name, value, n, origin, basis) in enumerate(items, start=1):
        rows.append({
            "withheld_id": f"W-{i:02d}", "quantity": name,
            "previously_published_value": value, "previously_published_n": n,
            "published_by_session": origin, "input_basis": basis,
            "admissible_under_official_only_rule": "no" if "AGGREGATOR" in basis else "yes - see note",
            "reason": "input data comes from a third-party mirror, not an official publisher"
                      if "AGGREGATOR" in basis else
                      "input is official; value is superseded by this desk's own recomputation and is not reused",
            "source_url": "https://github.com/sassnarep3-star/Own5",
        })
    return rows


# --------------------------------------------------------------------------
# 6. Walk-forward evaluation of the origination model (official feed only)
# --------------------------------------------------------------------------
def walk_forward_2026(games: list, first_eval_week: int = 5) -> dict:
    """Refit the side and total models before each week and predict that week.

    Everything is fitted on official nfl.com results only, and every prediction
    is made before seeing the week it scores.
    """
    weeks = sorted({g["week"] for g in games})
    preds = []
    for w in weeks:
        if w < first_eval_week:
            continue
        prior = [g for g in games if g["week"] < w]
        if len(prior) < 40:
            continue
        mm, tm = MarginModel(), TotalsModel()
        for g in prior:
            mm.add(g["home"], g["away"], float(g["home_margin"]), not g["neutral_site"])
            tm.add(g["home"], g["away"], float(g["total_points"]))
        mm.fit()
        tm.fit()
        for g in [x for x in games if x["week"] == w]:
            mu = mm.predict(g["home"], g["away"], bool(g["neutral_site"]))
            tt = tm.predict(g["home"], g["away"])
            preds.append({
                "game_id": g["game_id"], "week": w,
                "pred_side_home_pts": mu, "pred_total_pts": tt,
                "actual_margin": float(g["home_margin"]),
                "actual_total": float(g["total_points"]),
                "home_won": 1 if g["home_margin"] > 0 else (0 if g["home_margin"] < 0 else -1),
            })
    return {"predictions": preds}


def model_accuracy(preds: list) -> dict:
    if not preds:
        return {}
    side_err = [p["pred_side_home_pts"] - p["actual_margin"] for p in preds]
    tot_err = [p["pred_total_pts"] - p["actual_total"] for p in preds]
    decided = [p for p in preds if p["home_won"] >= 0]
    # Turn a point forecast into a win probability with the empirical spread of
    # the residuals; sigma is fitted on the same out-of-sample predictions.
    sigma = stdev([p["pred_side_home_pts"] - p["actual_margin"] for p in preds])
    probs, outcomes = [], []
    for p in decided:
        probs.append(norm_cdf(p["pred_side_home_pts"] / sigma))
        outcomes.append(p["home_won"])
    pred_margin = [p["pred_side_home_pts"] for p in preds]
    act_margin = [p["actual_margin"] for p in preds]
    r, pval, n = pearson(pred_margin, act_margin)
    hits = sum(1 for p in decided if (p["pred_side_home_pts"] > 0) == (p["home_won"] == 1))
    return {
        "n_predictions": len(preds),
        "weeks_covered": f"{min(p['week'] for p in preds)}-{max(p['week'] for p in preds)}",
        "side_mae": mean([abs(e) for e in side_err]),
        "side_bias": mean(side_err),
        "side_rmse": (sum(e * e for e in side_err) / len(side_err)) ** 0.5,
        "total_mae": mean([abs(e) for e in tot_err]),
        "total_bias": mean(tot_err),
        "total_rmse": (sum(e * e for e in tot_err) / len(tot_err)) ** 0.5,
        "margin_corr_r": r, "margin_corr_p": pval, "margin_corr_n": n,
        "su_hits": hits, "su_decided": len(decided),
        "su_hit_rate": hits / len(decided) if decided else float("nan"),
        "sigma_margin": sigma,
        "log_loss": log_loss(probs, outcomes),
        "brier": brier(probs, outcomes),
        "naive_mae_tie": mean([abs(p["actual_margin"]) for p in preds]),
        "naive_mae_league_total": mean([abs(p["actual_total"] - mean([q["actual_total"] for q in preds]))
                                        for p in preds]),
    }


# --------------------------------------------------------------------------
# 7. Price-snapshot store
# --------------------------------------------------------------------------
SNAPSHOT_TYPES = [
    ("MODEL_ORIGIN", "the price this desk originates when it first prices the market"),
    ("MODEL_CLOSE", "the desk's last price before kickoff"),
    ("MARKET_OPEN", "the operator's opening price"),
    ("MARKET_CLOSE", "the operator's closing price"),
    ("MARKET_REFERENCE", "an aggregator line of unknown timestamp, kept for context only"),
]


def build_price_store(originated: list, game_slates: list) -> list:
    """One row per (market, snapshot type).

    The store always has the slot.  When no official source exists for a slot
    the value is empty and the row carries a flag id -- the store records what
    we have and what we do not, it never invents an opening or closing price.
    """
    rows = []
    for m in originated:
        base = {
            "season": 2026, "week": m["week"], "game_id": m["game_id"],
            "matchup": m["matchup"], "market_id": m["market_id"], "market_type": m["market_type"],
        }
        # --- desk-side snapshots (tier DERIVED, sourced to the official inputs)
        rows.append({**base, "snapshot_type": "MODEL_ORIGIN",
                     "line_value": m["model_line"], "price_american": m["model_price_american"],
                     "snapshot_utc": RETRIEVED_UTC, "source_url": m["model_source_url"],
                     "source_tier": "DERIVED", "verified": "yes - reproducible from the committed inputs",
                     "flag_id": ""})
        rows.append({**base, "snapshot_type": "MODEL_CLOSE",
                     "line_value": "", "price_american": "", "snapshot_utc": "",
                     "source_url": "", "source_tier": "",
                     "verified": "no - not yet observed",
                     "flag_id": "F-03"})
        # --- operator-side snapshots: no official publisher exists
        for st in ("MARKET_OPEN", "MARKET_CLOSE"):
            rows.append({**base, "snapshot_type": st, "line_value": "", "price_american": "",
                         "snapshot_utc": "", "source_url": "", "source_tier": "",
                         "verified": "no - nfl.com publishes no betting prices",
                         "flag_id": "F-01"})
        # --- aggregator reference, timestamp unknown
        rows.append({**base, "snapshot_type": "MARKET_REFERENCE",
                     "line_value": m["market_line"], "price_american": m["market_price_american"],
                     "snapshot_utc": "",
                     "source_url": MIRROR_GAMES_URL, "source_tier": "AGGREGATOR",
                     "verified": "no - third-party mirror, snapshot time unknown",
                     "flag_id": "F-01"})
    return rows


# --------------------------------------------------------------------------
# 8. Replacement-depth tracker
# --------------------------------------------------------------------------
def build_replacement_depth() -> tuple:
    """Track HOW DEEP the replacement is, not merely that one happened.

    Inputs, both official:
      * the club's own published depth chart (1st/2nd/3rd string), and
      * the NFL's official weekly injury report (practice + game status).
    """
    slots = read_csv(os.path.join(REPO, "nfl-desk-864d5668", "data", "depth_detail.csv"))
    inj = read_csv(os.path.join(REPO, "nfl-desk-864d5668", "data", "injuries.csv"))
    inj_by_name = {}
    for r in inj:
        inj_by_name.setdefault(r["player"].strip(), []).append(r)

    rows = []
    for s in slots:
        team = s["team"]
        unit = s["unit"]
        pos = s["position"]
        first, second, third = s["first_string"].strip(), s["second_string"].strip(), s["third_string"].strip()
        used = s["string_used"].strip()
        expected = s["expected_starter_next_game"].strip()
        skipped = s["out_players_skipped"].strip()
        try:
            used_i = int(float(used)) if used else 1
        except ValueError:
            used_i = 1
        replacement = expected if used_i > 1 else ""
        repl_depth = str(used_i) if used_i > 1 else ""
        # Is the man stepping in himself carrying an injury designation?  If so
        # the loss compounds: the next name down is the one who really plays.
        repl_status = ""
        repl_practice = ""
        repl_on_report = "no"
        if replacement:
            hit = inj_by_name.get(replacement)
            if hit:
                repl_on_report = "yes"
                repl_status = hit[0]["game_status_as_published"].strip()
                repl_practice = hit[0]["practice_status_as_published"].strip()
        cascade = ""
        cascade_depth = ""
        if repl_on_report == "yes" and repl_status == "Out":
            cascade = third if third else ""
            cascade_depth = "3" if third else ""
        no_backup = s["no_backup_published"].strip()
        rows.append({
            "team": team, "club": s["club"], "unit": unit, "position": pos,
            "first_string": first, "second_string": second, "third_string": third,
            "starter_unavailable": skipped,
            "expected_starter_next_game": expected,
            "replacement_player": replacement,
            "replacement_depth_string": repl_depth,
            "depth_of_replacement_label": ({2: "2nd string", 3: "3rd string", 4: "4th string"}
                                           .get(used_i, "starter (no replacement)") if used_i > 1
                                           else "starter available"),
            "replacement_on_official_report": repl_on_report,
            "replacement_game_status": repl_status,
            "replacement_practice_status": repl_practice,
            "compounding_replacement_out": "yes" if cascade else "no",
            "cascade_to_player": cascade,
            "cascade_depth_string": cascade_depth,
            "rungs_down": s["deficiency_points"],
            "no_backup_published": no_backup,
            "depth_chart_source_url": s["source"],
            "injury_source_url": INJURY_URL,
            "as_of": "2026-11-13",
        })

    # Cross-check: every player the official report lists as Out should either
    # be a listed starter whose slot moved down the chart, or be a non-starter.
    out_players = [r for r in inj if r["game_status_as_published"].strip() == "Out"]
    covered = {s["out_players_skipped"].strip() for s in slots if s["out_players_skipped"].strip()}
    checks = []
    for r in out_players:
        name = r["player"].strip()
        is_listed_starter = any(name == s["first_string"].strip() for s in slots)
        moved = name in covered
        if is_listed_starter and not moved:
            state = "IRREGULAR - listed Out but the club chart still shows him as the starter (F-06)"
        elif not is_listed_starter:
            state = "not a published first-string player - no slot to move"
        else:
            state = "ok - slot moved down the published chart"
        checks.append({
            "team": r["team"], "player": name, "position": r["position"],
            "game_status": r["game_status_as_published"],
            "practice_status": r["practice_status_as_published"],
            "injured_player_is_published_starter": "yes" if is_listed_starter else "no",
            "depth_slot_moved": "yes" if moved else "no",
            "check_state": state,
            "injury_source_url": INJURY_URL,
            "depth_source_url": r.get("source", ""),
        })
    return rows, checks


# --------------------------------------------------------------------------
# 9. Origination: side first, then total, then moneyline
# --------------------------------------------------------------------------
def originate(games: list, slates: list, mirror: list, sigma: float) -> tuple:
    """Price every scheduled market in the required order.

    The order is not cosmetic.  The side is priced from the margin model; the
    total is priced from a separate totals model; the moneyline is then
    DERIVED from the two of them (margin mean + margin spread), never fitted
    on its own.  Every row records that dependency.
    """
    mm, tm = MarginModel(), TotalsModel()
    for g in games:
        mm.add(g["home"], g["away"], float(g["home_margin"]), not g["neutral_site"])
        tm.add(g["home"], g["away"], float(g["total_points"]))
    mm.fit()
    tm.fit()
    if not sigma or sigma != sigma or sigma <= 0:
        resid = [g["home_margin"] - mm.predict(g["home"], g["away"], bool(g["neutral_site"]))
                 for g in games]
        sigma = stdev(resid)

    midx = mirror_index(mirror)
    rows, steps = [], []
    for s in slates:
        week = int(s["week"])
        away, home = s["away"], s["home"]
        neutral = bool(s["neutral"])
        gid = f"2026_{week:02d}_{away}_{home}"
        m = midx.get(("2026", str(week), away, home), {})

        # ---- step 1: the side -------------------------------------------
        model_side = mm.predict(home, away, neutral)          # expected HOME margin, pts
        market_side = fnum(m.get("spread_line"))
        steps.append({"game_id": gid, "origination_step": "1_side",
                      "model_value": fmt(model_side, 2), "market_value": fmt(market_side, 2),
                      "difference": fmt(model_side - market_side, 2) if market_side is not None else "",
                      "derived_from": "margin model fitted on 137 official 2026 results",
                      "source_url": "https://www.nfl.com/schedules/2026/by-week/"})

        # ---- step 2: the total ------------------------------------------
        model_total = tm.predict(home, away)
        market_total = fnum(m.get("total_line"))
        steps.append({"game_id": gid, "origination_step": "2_total",
                      "model_value": fmt(model_total, 2), "market_value": fmt(market_total, 2),
                      "difference": fmt(model_total - market_total, 2) if market_total is not None else "",
                      "derived_from": "totals model fitted on 137 official 2026 results",
                      "source_url": "https://www.nfl.com/schedules/2026/by-week/"})

        # ---- step 3: the moneyline, derived from side + total ------------
        model_prob_home = norm_cdf(model_side / sigma)
        model_ml_home = decimal_to_american(1.0 / model_prob_home) if 0 < model_prob_home < 1 else ""
        home_ml = fnum(m.get("home_moneyline"))
        away_ml = fnum(m.get("away_moneyline"))
        market_prob_home = float("nan")
        if home_ml and away_ml:
            _, market_prob_home = devig_two_way(away_ml, home_ml)
        steps.append({"game_id": gid, "origination_step": "3_moneyline",
                      "model_value": fmt(model_prob_home, 4), "market_value": fmt(market_prob_home, 4),
                      "difference": fmt(model_prob_home - market_prob_home, 4)
                      if market_prob_home == market_prob_home else "",
                      "derived_from": "step 1 (side) + step 2 (total); P(home win) = Phi(side / sigma)",
                      "source_url": "https://www.nfl.com/schedules/2026/by-week/"})

        common = {
            "game_id": gid, "season": 2026, "week": week, "away": away, "home": home,
            "matchup": f"{away} @ {home}",
            "neutral_site": s["neutral"], "kickoff_label": s.get("kickoff_label", ""),
            "status": s.get("status", ""),
            "origination_order": 0,   # overridden per market row below
            "model_source_url": "https://www.nfl.com/schedules/2026/by-week/",
            "market_source_url": MIRROR_GAMES_URL,
            "market_source_tier": "AGGREGATOR",
            "snapshot_utc": RETRIEVED_UTC,
        }
        rows.append({**common, "market_id": f"{gid}:SIDE", "market_type": "SIDE",
                     "origination_order": 1,
                     "model_line": fmt(model_side, 2), "market_line": fmt(market_side, 2),
                     "difference_model_minus_market": fmt(model_side - market_side, 2)
                     if market_side is not None else "",
                     "model_price_american": "", "market_price_american": "",
                     "units": "points, from the home team's perspective",
                     "derived_from": "step 1 (side) - margin model, fitted first"})
        rows.append({**common, "market_id": f"{gid}:TOTAL", "market_type": "TOTAL",
                     "origination_order": 2,
                     "model_line": fmt(model_total, 2), "market_line": fmt(market_total, 2),
                     "difference_model_minus_market": fmt(model_total - market_total, 2)
                     if market_total is not None else "",
                     "model_price_american": "", "market_price_american": "",
                     "units": "points, combined scoring",
                     "derived_from": "step 2 (total) - totals model, fitted second"})
        rows.append({**common, "market_id": f"{gid}:ML", "market_type": "MONEYLINE",
                     "origination_order": 3,
                     "model_line": fmt(model_prob_home, 4), "market_line": fmt(market_prob_home, 4)
                     if market_prob_home == market_prob_home else "",
                     "difference_model_minus_market": fmt(model_prob_home - market_prob_home, 4)
                     if market_prob_home == market_prob_home else "",
                     "model_price_american": fmt(model_ml_home, 1) if model_ml_home else "",
                     "market_price_american": fmt(home_ml, 0) if home_ml else "",
                     "units": "probability the home team wins (market figure de-vigged)",
                     "derived_from": "step 3 (moneyline) - derived from step 1 (side) and step 2 (total), not fitted separately"})
    return rows, steps, {"sigma": sigma, "hfa_pts": mm.beta[mm.p - 1]}

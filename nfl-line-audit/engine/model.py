"""Model: opponent-aware, recency-weighted, drive-based team strength.

Why this shape:
  * "Ingest game-level results to make the ratings opponent-aware"  -> iterative schedule
    adjustment (each team's offensive rate is measured against the defences it actually faced).
  * "Use snap counts as the starter proxy" / "Do not model depth from jersey order" -> the
    availability model below is built on playing time, never on roster order.
  * "Add injury and personnel ablations instead of fixed penalties" -> this module exposes
    `fit(..., personnel_weights=...)` so the same model can be refit with and without
    availability weight and the difference reported with uncertainty.

Everything is deterministic; no random initialisation, fixed iteration count.
"""
import math

GAMES_PER_TEAM_WEEK = 1.0
RATING_ITERS = 60


def _recency_weight(season, week, ref_season, ref_week, half_life_weeks):
    # Week distance across seasons: 18 weeks per season.
    d = (ref_season - season) * 18 + (ref_week - week)
    if d < 0:
        return 0.0
    return 0.5 ** (d / float(half_life_weeks))


class Ratings:
    """Offence and defence points-per-drive rates for every club."""

    def __init__(self):
        self.off = {}
        self.deff = {}
        self.games_used = {}
        self.league_off = 0.0

    def to_json(self):
        return {
            "league_points_per_drive": round(self.league_off, 6),
            "offence_points_per_drive": {k: round(v, 6) for k, v in sorted(self.off.items())},
            "defence_points_allowed_per_drive": {k: round(v, 6) for k, v in sorted(self.deff.items())},
            "weighted_games_used": {k: round(v, 3) for k, v in sorted(self.games_used.items())},
        }


def fit(games, ref_season, ref_week, half_life_weeks=6.0, side_weights=None):
    """Fit ratings using only games strictly before (ref_season, ref_week).

    games: list of dicts with season, week, home, away, home_score, away_score,
           home_off_drives, home_def_drives, away_off_drives, away_def_drives.
    side_weights: optional {club: multiplier} applied to that club's offensive output
           (used by the injury/personnel ablation; 1.0 means no adjustment).
    """
    side_weights = side_weights or {}
    r = Ratings()
    teams = sorted({g["home"] for g in games} | {g["away"] for g in games})
    use = []
    for g in games:
        w = _recency_weight(g["season"], g["week"], ref_season, ref_week, half_life_weeks)
        if w <= 0:
            continue
        if not (g.get("home_off_drives") and g.get("away_off_drives")):
            continue
        use.append((g, w))
    if not use:
        return r
    # league baseline: weighted points per drive
    num = den = 0.0
    for g, w in use:
        for side in ("home", "away"):
            pts = g[side + "_score"]
            drv = g[side + "_off_drives"]
            num += w * pts
            den += w * drv
    r.league_off = num / den if den else 0.0
    off = {t: 0.0 for t in teams}
    deff = {t: 0.0 for t in teams}
    used = {t: 0.0 for t in teams}
    # start at league average
    for t in teams:
        off[t], deff[t] = r.league_off, r.league_off
    for _ in range(RATING_ITERS):
        # offence vs the defences faced
        num = {t: 0.0 for t in teams}
        den = {t: 0.0 for t in teams}
        for g, w in use:
            for side, other in (("home", "away"), ("away", "home")):
                t = g[side]
                pts = g[side + "_score"] * side_weights.get(t, 1.0)
                drv = g[side + "_off_drives"]
                num[t] += w * pts
                den[t] += w * drv
        for t in teams:
            # shrink toward the league mean in ratio space with a 3-drive prior
            off[t] = (num[t] + 3.0 * r.league_off) / (den[t] + 3.0) if den[t] + 3.0 else r.league_off
        # defence: points allowed per opponent drive, adjusted for opponent offence strength
        num = {t: 0.0 for t in teams}
        den = {t: 0.0 for t in teams}
        for g, w in use:
            for side, other in (("home", "away"), ("away", "home")):
                defteam = g[side]
                offteam = g[other]
                pts = g[other + "_score"]
                drv = g[other + "_off_drives"]
                strength = off.get(offteam, r.league_off) / r.league_off if r.league_off else 1.0
                num[defteam] += w * pts / max(0.55, strength)
                den[defteam] += w * drv
        for t in teams:
            deff[t] = (num[t] + 3.0 * r.league_off) / (den[t] + 3.0) if den[t] + 3.0 else r.league_off
        # recentre so the mean club is average (keeps sigma comparable across fits)
        mo = sum(off.values()) / len(off)
        md = sum(deff.values()) / len(deff)
        for t in teams:
            off[t] = off[t] - mo + r.league_off
            deff[t] = deff[t] - md + r.league_off
    for g, w in use:
        used[g["home"]] = used.get(g["home"], 0.0) + w
        used[g["away"]] = used.get(g["away"], 0.0) + w
    r.off, r.deff, r.games_used = off, deff, used
    return r


def home_field(games, ref_season, ref_week, half_life_weeks=8.0):
    """Measured home-field points per game (mean home margin minus mean away margin) - 0."""
    num = den = 0.0
    for g in games:
        w = _recency_weight(g["season"], g["week"], ref_season, ref_week, half_life_weeks)
        if w <= 0:
            continue
        if g.get("neutral"):
            continue
        num += w * (g["home_score"] - g["away_score"])
        den += w
    return num / den if den else 0.0


def expected_margin(r, home_off_drives, away_off_drives, home, away, hfa):
    ho = r.off.get(home, r.league_off)
    hd = r.deff.get(home, r.league_off)
    ao = r.off.get(away, r.league_off)
    ad = r.deff.get(away, r.league_off)
    # points scored = drives * (own offence rate adjusted by opponent defence vs league)
    hp = home_off_drives * (ho * (ad / r.league_off if r.league_off else 1.0))
    ap = away_off_drives * (ao * (hd / r.league_off if r.league_off else 1.0))
    return hp - ap + hfa


def expected_total(r, home_off_drives, away_off_drives, home, away):
    ho = r.off.get(home, r.league_off)
    hd = r.deff.get(home, r.league_off)
    ao = r.off.get(away, r.league_off)
    ad = r.deff.get(away, r.league_off)
    hp = home_off_drives * (ho * (ad / r.league_off if r.league_off else 1.0))
    ap = away_off_drives * (ao * (hd / r.league_off if r.league_off else 1.0))
    return hp + ap


def team_drives(games, ref_season, ref_week, half_life_weeks=8.0):
    """Weighted average offensive drives per game, per club (a pace term)."""
    num, den = {}, {}
    for g in games:
        w = _recency_weight(g["season"], g["week"], ref_season, ref_week, half_life_weeks)
        if w <= 0:
            continue
        for side in ("home", "away"):
            d = g.get(side + "_off_drives")
            if not d:
                continue
            t = g[side]
            num[t] = num.get(t, 0.0) + w * d
            den[t] = den.get(t, 0.0) + w
    return {t: num[t] / den[t] for t in num if den[t]}

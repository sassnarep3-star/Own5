#!/usr/bin/env python3
"""Per-game official final links for the 2026 season.

The prior desk (session 3fb93d11) transcribed 136 official finals from nfl.com week
pages on 2026-11-14, one row each with the week-page URL. A week page URL is a weak
provenance link: the reader cannot jump to the game. nfl.com publishes a stable
per-game page, and the game id in the mirror already encodes it, so this module builds
`https://www.nfl.com/games/<away-slug>-at-<home-slug>-2026-reg-<week>` and records
both links. The slug is taken from the club page names on the week pages
(e.g. 'commanders-at-giants-2026-reg-10').

Nothing here changes a score: scores come from the official week pages via
build_results.py. This module only supplies the per-game URL.
"""

SLUG = {
    "AZ": "cardinals", "ATL": "falcons", "BAL": "ravens", "BUF": "bills",
    "CAR": "panthers", "CHI": "bears", "CIN": "bengals", "CLE": "browns",
    "DAL": "cowboys", "DEN": "broncos", "DET": "lions", "GB": "packers",
    "HOU": "texans", "IND": "colts", "JAX": "jaguars", "KC": "chiefs",
    "LA": "rams", "LAC": "chargers", "LV": "raiders", "MIA": "dolphins",
    "MIN": "vikings", "NE": "patriots", "NO": "saints", "NYG": "giants",
    "NYJ": "jets", "PHI": "eagles", "PIT": "steelers", "SEA": "seahawks",
    "SF": "49ers", "TB": "buccaneers", "TEN": "titans", "WAS": "commanders",
}

# Verified against the live Week 10 page (2026-11-15): the page's own links read
#   /games/commanders-at-giants-2026-reg-10
#   /games/patriots-at-lions-2026-reg-10
#   /games/chiefs-at-falcons-2026-reg-10
#   /games/texans-at-browns-2026-reg-10
#   /games/vikings-at-packers-2026-reg-10
#   /games/dolphins-at-colts-2026-reg-10
#   /games/panthers-at-saints-2026-reg-10
#   /games/bills-at-jets-2026-reg-10
#   /games/jaguars-at-titans-2026-reg-10
#   /games/rams-at-cardinals-2026-reg-10   /games/seahawks-at-raiders-2026-reg-10
#   /games/49ers-at-cowboys-2026-reg-10    /games/steelers-at-bengals-2026-reg-10
#   /games/chargers-at-ravens-2026-reg-10
# For weeks 1-9 the same construction is applied; those URLs are published as
# CONSTRUCTED and flagged, because this session did not open all 136 game pages.
VERIFIED_WEEK10 = {
    "2026_10_WAS_NYG", "2026_10_NE_DET", "2026_10_KC_ATL", "2026_10_HOU_CLE",
    "2026_10_MIN_GB", "2026_10_MIA_IND", "2026_10_CAR_NO", "2026_10_BUF_NYJ",
    "2026_10_JAX_TEN", "2026_10_LA_ARI", "2026_10_SEA_LV", "2026_10_SF_DAL",
    "2026_10_PIT_CIN", "2026_10_LAC_BAL",
}


def game_url(away, home, week, game_id=None, week_page=None):
    """Return (url, status). Status is VERIFIED or CONSTRUCTED."""
    week = int(week)
    away_slug = SLUG.get(away)
    home_slug = SLUG.get(home)
    if not away_slug or not home_slug:
        return "", "NO SLUG"
    url = "https://www.nfl.com/games/%s-at-%s-2026-reg-%d" % (away_slug, home_slug, week)
    if game_id and game_id in VERIFIED_WEEK10:
        return url, "VERIFIED TODAY"
    return url, "CONSTRUCTED"

"""Parser for the official NFL.com weekly injury report (nfl.com/injuries/league/2026/regN).

Design rules (from the session brief and COORDINATION.md):
  * Pinned markup: the parser requires the exact table header, exactly two team tables and two
    team abbreviations per game unit. Any miss raises DriftError so the capture job fails loudly.
  * Nothing is inferred. A blank injury / game-status cell stays blank. Unknown enumerations are
    reported as flags, never mapped to a value.
  * Every row carries the page URL and the player's official profile link (nfl.com/players/...).
"""
import html
import re

EXPECTED_HEADER = ["Player", "Position", "Injuries", "Practice Status", "Game Status"]
# NFL.com club abbreviations as they appear in the injury report matchup strips.
NFL_CLUBS = {
    "AZ", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE", "DAL", "DEN", "DET", "GB",
    "HOU", "IND", "JAX", "KC", "LAC", "LAR", "LV", "MIA", "MIN", "NE", "NO", "NYG", "NYJ",
    "PHI", "PIT", "SEA", "SF", "TB", "TEN", "WAS",
}
# Values observed in the Week 10 capture. An unseen value is flagged for review, not mapped.
KNOWN_PRACTICE = {
    "Full Participation in Practice", "Limited Participation in Practice",
    "Did Not Participate In Practice",
}
KNOWN_GAME = {"Out", "Questionable", "Doubtful", ""}


class DriftError(RuntimeError):
    """Raised when the page no longer matches the pinned structure."""


def _text(fragment):
    fragment = re.sub(r"<[^>]+>", " ", fragment)
    return re.sub(r"\s+", " ", html.unescape(fragment)).strip()


def page_week(page_html, final_url):
    """Week number the page actually serves (from the URL and the title)."""
    m_url = re.search(r"/injuries/league/(\d{4})/reg(\d+)", final_url)
    m_title = re.search(r"<title>Official NFL Injury Report for Players - Week (\d+) of the (\d{4}) Season", page_html)
    url_week = int(m_url.group(2)) if m_url else None
    title_week = int(m_title.group(1)) if m_title else None
    season = int(m_title.group(2)) if m_title else (int(m_url.group(1)) if m_url else None)
    return {"url_week": url_week, "title_week": title_week, "season": season}


def parse(page_html, source_url):
    """Return (rows, summary). Raises DriftError on structural drift."""
    flags = []
    units = re.split(r'<section class="nfl-o-injury-report__unit">', page_html)
    if len(units) < 2:
        raise DriftError("no nfl-o-injury-report__unit sections found")
    # day headings in document order
    day_pos = [(m.start(), _text(m.group(1))) for m in re.finditer(r'<h2 class="d3-o-section-title">(.*?)</h2>', page_html, re.S)]
    unit_offsets = []
    cursor = 0
    for chunk in units[:-1]:
        cursor += len(chunk)
        unit_offsets.append(cursor)
        cursor += len('<section class="nfl-o-injury-report__unit">')
    rows = []
    games = []
    for idx, unit in enumerate(units[1:]):
        start = unit_offsets[idx]
        days_before = [d for p, d in day_pos if p < start]
        if not days_before:
            raise DriftError("game unit without a day heading")
        game_day = days_before[-1]
        tm = re.search(r'<span class="nfl-c-matchup-strip__date-time">(.*?)</span>\s*<span class="nfl-c-matchup-strip__date-timezone">(.*?)</span>', unit, re.S)
        if not tm:
            raise DriftError("game unit without kickoff time")
        kickoff = _text(tm.group(1))
        tz = _text(tm.group(2))
        nets = re.search(r'<p class="nfl-c-matchup-strip__networks">(.*?)</p>', unit, re.S)
        network = _text(nets.group(1)) if nets else ""
        abbrs = [_text(a) for a in re.findall(r'nfl-c-matchup-strip__team-abbreviation">(.*?)</span>', unit, re.S)]
        if len(abbrs) != 2:
            raise DriftError(f"expected 2 team abbreviations, found {len(abbrs)}")
        for a in abbrs:
            if a not in NFL_CLUBS:
                raise DriftError(f"unknown club abbreviation {a!r}")
        tables = re.findall(r'<table class="d3-o-table[^"]*">(.*?)</table>', unit, re.S)
        titles = re.findall(r'<div class="d3-o-section-sub-title"><span>(.*?)</span>', unit, re.S)
        if len(tables) != 2 or len(titles) != 2:
            raise DriftError(f"expected 2 team tables, found {len(tables)} tables / {len(titles)} titles")
        game_key = f"{game_day}|{abbrs[0]}@{abbrs[1]}"
        games.append({"game_day": game_day, "kickoff_local": kickoff, "timezone": tz,
                      "network": network, "away_abbr": abbrs[0], "home_abbr": abbrs[1],
                      "game_key": game_key})
        for team_pos, (tbl, title) in enumerate(zip(tables, titles)):
            team_abbr = abbrs[team_pos]  # first unit table = first matchup-strip club (away, then home)
            team_name = _text(title)
            head = re.search(r"<thead>(.*?)</thead>", tbl, re.S)
            if not head:
                raise DriftError(f"{team_abbr}: table has no thead")
            heads = [_text(h) for h in re.findall(r"<th[^>]*>(.*?)</th>", head.group(1), re.S)]
            if heads != EXPECTED_HEADER:
                raise DriftError(f"{team_abbr}: header {heads} != {EXPECTED_HEADER}")
            body = re.search(r"<tbody>(.*?)</tbody>", tbl, re.S)
            body_html = body.group(1) if body else ""
            for r_idx, tr in enumerate(re.findall(r"<tr>(.*?)</tr>", body_html, re.S), start=1):
                cells = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
                if len(cells) != 5:
                    raise DriftError(f"{team_abbr} row {r_idx}: {len(cells)} cells, expected 5")
                href = re.search(r'href="(/players/[^"]+)"', cells[0])
                player = _text(cells[0])
                pos, inj, prac, game = (_text(c) for c in cells[1:])
                if not player:
                    raise DriftError(f"{team_abbr} row {r_idx}: blank player name")
                if not pos:
                    raise DriftError(f"{team_abbr} row {r_idx} ({player}): blank position")
                if not prac:
                    raise DriftError(f"{team_abbr} row {r_idx} ({player}): blank practice status")
                if prac not in KNOWN_PRACTICE:
                    flags.append(f"unknown practice status {prac!r} ({player})")
                if game not in KNOWN_GAME:
                    flags.append(f"unknown game status {game!r} ({player})")
                rows.append({
                    "game_key": game_key, "game_day": game_day, "kickoff_local": kickoff,
                    "timezone": tz, "network": network, "team_abbr": team_abbr,
                    "team_name": team_name, "player": player,
                    "player_profile_url": ("https://www.nfl.com" + href.group(1)) if href else "",
                    "position": pos, "injuries": inj, "practice_status": prac,
                    "game_status": game, "source_url": source_url,
                })
    summary = {
        "games": len(games), "team_tables": len(games) * 2, "rows": len(rows),
        "teams": len({r["team_abbr"] for r in rows}),
        "flags": sorted(set(flags)),
        "clubs_seen": sorted({g["away_abbr"] for g in games} | {g["home_abbr"] for g in games}),
    }
    if len(summary["clubs_seen"]) != 32:
        flags.append(f"clubs seen = {len(summary['clubs_seen'])}, expected 32")
        summary["flags"] = sorted(set(flags))
    return rows, games, summary

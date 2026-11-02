"""Parse frozen, human-read official excerpts. No network and no missing-value imputation.

Run from the repository root: python research/build_snapshot.py
The evidence is a dated snapshot, not a claim that the upstream page is immutable.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EV = ROOT / "research/evidence"
RETRIEVED = "2026-11-02"

SOURCE_ROWS = [
    ("S01", "National Football League", "2026 Official Playing Rules", "https://static.www.nfl.com/image/upload/fl_attachment/league/tqivdkzt9mu6wdgsh1ku.pdf", "Official NFL PDF; Rule 11-1-2 extracted by official-domain search", "nfl_rules.md"),
    ("S02", "NFL Football Operations", "Featured rules — 2025 overtime change", "https://operations.nfl.com/rules-officiating/featured-rules", "Rendered official page read", "nfl_rules.md"),
    ("S03", "NFL Support", "Game Books", "https://support.nfl.com/hc/en-us/articles/35869678028180-Game-Books", "Rendered official page read", "nfl_rules.md"),
    ("S04", "NFL GSIS", "About Game Statistics and Information System", "https://www.nflgsis.com/Help/About.html", "Rendered official help read; schedule endpoint requires login", "nfl_rules.md"),
    ("S05", "NFL Support", "Who is making these odds?", "https://support.nfl.com/hc/en-us/articles/35869738523412-Who-is-making-the-odds", "Rendered official page read", "nfl_rules.md"),
    ("S06", "NFL Support", "What is a total?", "https://support.nfl.com/hc/en-us/articles/35869727578900-What-is-a-total", "Rendered official page read", "nfl_rules.md"),
    ("S07", "NFL Support", "Moneyline explanation under a point-spread URL", "https://support.nfl.com/hc/en-us/articles/35869774194324-What-is-the-point-spread", "Rendered official page read; title/content mismatch flagged", "nfl_rules.md"),
    ("S08", "NFL Next Gen Stats", "Introduction to Completion Probability", "https://www.nfl.com/news/next-gen-stats-introduction-to-completion-probability-0ap3000000964655", "Rendered official article read", "nfl_rules.md"),
    ("S09", "FanDuel", "Football with FanDuel", "https://support.fanduel.com/s/article/Betting-football-with-FanDuel", "Rendered official operator help read", "fanduel_football.md"),
    ("S10", "National Football League", "2026 regular-season league standings snapshot", "https://www.nfl.com/standings/league/2026/REG", "All 32 rendered rows read; Houston cross-read on official division view", "nfl_standings_2026.md"),
    ("S11", "National Football League", "2026 Week 9 schedule snapshot", "https://www.nfl.com/schedules/2026/by-week/week-9", "All 15 rendered game links and bye teams read", "nfl_week9_2026.md"),
    ("S12", "National Football League", "Joe Burrow 2024 regular-season log", "https://www.nfl.com/players/joe-burrow/stats/logs/2024/", "All 17 regular-season rows read; preseason excluded", "burrow_logs_2024.md"),
    ("S13", "National Football League", "Ja’Marr Chase 2024 regular-season log", "https://www.nfl.com/players/ja-marr-chase/stats/logs/2024/", "All 17 regular-season rows read; preseason excluded", "chase_logs_2024.md"),
    ("S14", "National Football League", "Joe Burrow career statistics", "https://www.nfl.com/players/joe-burrow/stats/career", "2024 row read as reconciliation control", "career_reconciliation.md"),
    ("S15", "National Football League", "Ja’Marr Chase career statistics", "https://www.nfl.com/players/ja-marr-chase/stats/career", "2024 row read as reconciliation control", "career_reconciliation.md"),
    ("S16", "Oxford University Press / Review of Financial Studies", "Harvey, Liu & Zhu — …and the Cross-Section of Expected Returns", "https://academic.oup.com/rfs/issue/29/1", "Official publisher issue and DOI verified by search; methodology reference only", ""),
    ("S17", "American Meteorological Society", "Brier (1950) bibliographic reference", "https://journals.ametsoc.org/view/journals/mwre/148/9/mwrD190076.xml?tab_body=fulltext-display", "Official journal reference list verified by search; not an NFL source", ""),
]


def dump(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def cells(line: str) -> list[str]:
    return [x.strip() for x in line.strip().strip("|").split("|")]


def build() -> dict:
    sources = [dict(id=i, publisher=p, title=t, url=u, access_method=m,
                    retrieved_utc=RETRIEVED, status="official content inspected",
                    evidence_file="research/evidence/" + f if f else None,
                    evidence_sha256=hashlib.sha256((EV / f).read_bytes()).hexdigest() if f else None)
               for i, p, t, u, m, f in SOURCE_ROWS]
    source = {s["id"]: s for s in sources}
    teams = []
    for line in (EV / "nfl_standings_2026.md").read_text().splitlines():
        if not line.startswith("| [![]("):
            continue
        code = re.search(r"/logos/([A-Z]+)", line).group(1)
        name = re.search(r"\\<br>\\<br>([^\\]+)\\<br>", line).group(1)
        url = re.search(r"\]\((https://www\.nfl\.com/teams/[^)]+)\)", line).group(1)
        c = cells(line)[1:]
        assert len(c) == 16, (code, len(c))
        teams.append(dict(team_code=code, team=name, team_url=url,
                          wins=int(c[0]), losses=int(c[1]), ties=int(c[2]),
                          points_for=int(c[4]), points_against=int(c[5]),
                          source_id="S10", source_url=source["S10"]["url"],
                          evidence_file="research/evidence/nfl_standings_2026.md",
                          evidence_line=line, verified=True))
    assert len(teams) == 32
    assert len({t["team_code"] for t in teams}) == 32
    assert sum(t["points_for"] for t in teams) == sum(t["points_against"] for t in teams)
    bycode = {t["team_code"]: t for t in teams}
    aliases = {t["team"].split()[-1]: t["team_code"] for t in teams}
    aliases["49ers"] = "SF"
    schedule = []
    for line in (EV / "nfl_week9_2026.md").read_text().splitlines():
        m = re.match(r"\[(.+) at (.+), (\w+), November (\d+)(?:st|nd|rd|th), (\d+:\d+ [AP]M), ([^\]]+)\]\((https://www\.nfl\.com/games/([^)]+))\)", line)
        if not m:
            continue
        away, home, weekday, day, time, channel, url, slug = m.groups()
        schedule.append(dict(game_id=slug, season=2026, week=9,
                             away=aliases[away], home=aliases[home],
                             away_name=bycode[aliases[away]]["team"],
                             home_name=bycode[aliases[home]]["team"],
                             date=f"2026-11-{int(day):02d}", local_time=time,
                             timezone_label="LOCAL (venue local; not converted)",
                             broadcast=channel,
                             neutral_site=True if slug == "bengals-at-falcons-2026-reg-9" else None,
                             source_id="S11", source_url=url,
                             evidence_file="research/evidence/nfl_week9_2026.md",
                             evidence_line=line, verified=True))
    assert len(schedule) == 15
    assert len({t for g in schedule for t in (g["home"], g["away"])} | {"PIT", "TEN"}) == 32
    logs = {}
    for player, filename, sid in [("burrow", "burrow_logs_2024.md", "S12"), ("chase", "chase_logs_2024.md", "S13")]:
        rows = []
        for line in (EV / filename).read_text().splitlines():
            if not re.match(r"\| \d+ \|", line):
                continue
            c = cells(line)
            month, day, year = c[1].split("/")
            rows.append(dict(season=2024, week=int(c[0]), date=f"{year}-{month}-{day}",
                             opponent=c[2], result=c[3],
                             passing_yards=int(c[6]) if player == "burrow" else None,
                             receptions=int(c[4]) if player == "chase" else None,
                             receiving_yards=int(c[5]) if player == "chase" else None,
                             source_id=sid, source_url=source[sid]["url"],
                             evidence_file="research/evidence/" + filename,
                             evidence_line=line, verified=True))
        assert len(rows) == 17
        logs[player] = sorted(rows, key=lambda r: r["week"])
    assert [r["week"] for r in logs["burrow"]] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14, 15, 16, 17, 18]
    assert sum(r["passing_yards"] for r in logs["burrow"]) == 4918
    assert sum(r["receiving_yards"] for r in logs["chase"]) == 1708
    assert sum(r["receptions"] for r in logs["chase"]) == 127
    paired = []
    for b, c in zip(logs["burrow"], logs["chase"]):
        assert (b["week"], b["date"], b["opponent"], b["result"]) == (c["week"], c["date"], c["opponent"], c["result"])
        paired.append(dict(season=2024, week=b["week"], date=b["date"], opponent=b["opponent"],
                           result=b["result"], burrow_passing_yards=b["passing_yards"],
                           chase_receptions=c["receptions"], chase_receiving_yards=c["receiving_yards"],
                           source_ids=["S12", "S13"], source_urls=[b["source_url"], c["source_url"]],
                           evidence_files=[b["evidence_file"], c["evidence_file"]],
                           evidence_lines=[b["evidence_line"], c["evidence_line"]], verified=True))
    snapshot = dict(retrieved_utc=RETRIEVED,
                    scope="Frozen official-source excerpts; not a complete historical database or live market feed.",
                    teams=teams, schedule=schedule, player_logs=logs, paired_player_games=paired,
                    market_quotes=[], settlement_events=[],
                    reconciliation=dict(team_points_for=sum(t["points_for"] for t in teams),
                                        team_points_against=sum(t["points_against"] for t in teams),
                                        burrow_passing_yards=4918, chase_receiving_yards=1708,
                                        chase_receptions=127))
    facts = []
    for t in teams:
        facts.append(dict(id="team-" + t["team_code"], category="Official snapshot", subject=t["team"],
                          values={k: t[k] for k in ("wins", "losses", "ties", "points_for", "points_against")},
                          source_ids=["S10"], source_urls=[t["source_url"]],
                          evidence_file=t["evidence_file"], evidence_line=t["evidence_line"], verified=True))
    for g in schedule:
        facts.append(dict(id="schedule-" + g["game_id"], category="Official schedule",
                          subject=g["away_name"] + " at " + g["home_name"],
                          values={k: g[k] for k in ("date", "local_time", "broadcast")},
                          source_ids=["S11"], source_urls=[g["source_url"]],
                          evidence_file=g["evidence_file"], evidence_line=g["evidence_line"], verified=True))
    for r in paired:
        facts.append(dict(id=f"paired-2024-{r['week']:02d}", category="Official player logs",
                          subject=f"2024 Week {r['week']} · Bengals {r['opponent']}",
                          values={k: r[k] for k in ("burrow_passing_yards", "chase_receptions", "chase_receiving_yards")},
                          source_ids=r["source_ids"], source_urls=r["source_urls"],
                          evidence_file=r["evidence_files"][0], evidence_line=r["evidence_lines"][0],
                          additional_evidence_file=r["evidence_files"][1],
                          additional_evidence_line=r["evidence_lines"][1], verified=True))
    quoted = [
        ("score-touchdown", "Scoring", "Touchdown", 6, "S01", "(a) Touchdown: 6 points"),
        ("score-field-goal", "Scoring", "Field goal", 3, "S01", "(b) Field goal: 3 points"),
        ("score-safety", "Scoring", "Safety", 2, "S01", "(c) Safety: 2 points"),
        ("score-try", "Scoring", "Try after touchdown", "1 point (field goal or safety) or 2 points (touchdown)", "S01", "(d) Try after touchdown: 1 point (field goal or safety) or 2 points (touchdown)"),
        ("ot-2025", "Rules", "2025 regular-season overtime change", "Both teams get a possession opportunity, subject to a 10-minute period", "S02", "NFL teams adopted to align the postseason and regular season overtime rules by granting both teams an opportunity to possess the ball regardless of the outcome of the first possession, subject to a 10-minute overtime period in the regular season."),
        ("gamebooks", "Data", "NFL Game Book", "PDF containing every score and stat from the game", "S03", "At the bottom of the Recap, there should be a Download Game Book PDF containing every score and stat from the game."),
        ("gsis-corrections", "Data", "GSIS statistical corrections", "Corrections made with Elias Sports Bureau", "S04", "Corrections to existing game information will be made regularly in conjunction with Elias Sports Bureau, the official statistician of the NFL."),
        ("odds-providers", "Markets", "NFL widget odds providers", "FanDuel, Caesars, and DraftKings", "S05", "Odds are provided by the official sportsbook partners of the NFL: FanDuel, Caesars, and DraftKings."),
        ("total-ot", "Markets", "NFL Support total definition", "Combined points, including overtime", "S06", "A total is a bet on the number of points scored in the game by both teams combined, including overtime."),
        ("moneyline-tie", "Markets", "NFL Support moneyline example", "Tie returns the stake in this example", "S07", "If the game ends in a tie, the bettor's wager is returned with no loss or profit."),
        ("ngs-inputs", "Signals", "Completion Probability inputs", "Air distance, air yards, receiver/defender separation, pass-rusher distance, QB speed, and other tracking inputs", "S08", "Those inputs include pass air distance (from quarterback to receiver), air yards, the distance between the receiver and the nearest defender, the distance between the quarterback and the nearest pass rusher, the speed of the quarterback at throw, among several other metrics."),
        ("fanduel-snap", "Settlement", "FanDuel NFL player-prop participation", "Active and at least one snap; otherwise applicable props void", "S09", "NFL player props are settled as normal if the player is active and plays at least one snap. If the player is inactive, or active but does not play a snap, applicable player prop bets are void."),
        ("fanduel-td", "Settlement", "FanDuel touchdown scorer", "A passing touchdown does not make the passer a touchdown scorer", "S09", "A player who throws a touchdown pass is NOT considered the touchdown scorer."),
        ("fanduel-two-point", "Settlement", "FanDuel two-point conversion statistics", "Yards and receptions on a two-point attempt excluded from standard totals", "S09", "Yards and receptions recorded during a two-point attempt do not count toward standard yardage or reception totals."),
    ]
    for i, cat, sub, val, sid, quote in quoted:
        facts.append(dict(id=i, category=cat, subject=sub, values={"value": val},
                          source_ids=[sid], source_urls=[source[sid]["url"]],
                          evidence_file=source[sid]["evidence_file"], evidence_line=quote, verified=True))
    reviews = [
        ("R01", "Missing market inputs", "All Week 9 games", "sportsbook_spread,sportsbook_total,american_odds,quote_timestamp,bookmaker,limits", "S11", "No official, timestamped sportsbook quote was captured. NFL schedule pages are not a price archive. Own fair lines are shown separately; market edge and CLV remain blank.", "Collect authorized operator feeds with pre-kickoff timestamps and retain the original response."),
        ("R02", "Missing player-prop market", "Current player props", "player,prop_line,over_price,under_price,quote_timestamp,participation_status", "S09", "No current operator prop quote or participation snapshot was verified. Historical 2024 thresholds are research examples, not current betting lines.", "Capture operator-specific props and official participation evidence before evaluation."),
        ("R03", "No economic validation", "All strategies", "net_roi,roi_lower_bound,clv,clv_lower_bound,out_of_sample_bets,holdout_result", "S16", "No strategy has the pre-registered out-of-sample market history required by the gates. No profit, skill, or reward claim is made.", "Run the locked protocol on future, untouched observations; never backfill a holdout with guesses."),
        ("R04", "Correlation scope", "Same-game combinations", "current_pair_correlation,joint_probability,sgp_fair_price", "S12", "The 2024 Burrow–Chase correlation is a 17-game, single-team historical estimate. It is not a current-season or universal SGP correlation.", "Estimate on broader matched game logs with uncertainty and out-of-sample joint calibration."),
        ("R05", "Model assumptions", "Own game lines", "empirical_home_advantage,injury_adjustment,weather_adjustment,starters", "S10", "Home advantage is disabled (zero assumption), not estimated. Injury, weather, roster and quarterback adjustments are unavailable and left blank. International venue is flagged.", "Verify point-in-time inputs; estimate adjustments only in training folds."),
        ("R06", "Source title mismatch", "NFL Support point-spread article", "", "S07", "The URL says point spread, but the retrieved article explains moneylines. It is not used as a spread definition.", "Review the official article; obtain a correct spread reference before adding one."),
        ("R07", "Dynamic-source discrepancy", "Ja’Marr Chase career page", "", "S15", "A search-index excerpt showed an older 2026 row than the rendered official page. Only the rendered 2024 row is used here; search snippets are not treated as live data.", "Use frozen rendered evidence and re-read the official page on refresh."),
        ("R08", "Access limitation", "NFL GSIS schedule", "", "S04", "The public help page describes official game books, but the schedule endpoint redirected to a login/error page. No authenticated or bulk GSIS data was obtained.", "Use publicly available NFL Game Center links or an authorized GSIS arrangement."),
        ("R09", "Slug irregularity", "Chase player logs", "", "S13", "The guessed jamarr-chase URL returned a player.DisplayName placeholder. The verified ja-marr-chase URL returned the actual named log and is the only player-log source used.", "Keep canonical official URLs in the source register; never accept placeholder pages."),
        ("R10", "Sample selection", "Historical prop study", "", "S12", "The study deliberately selects one QB–receiver pair and one completed season. It is descriptive and susceptible to selection bias; it is not a league-wide edge discovery.", "Pre-register a league-wide universe and evaluate untouched seasons."),
        ("R11", "Settlement variability", "Parlays and player props", "operator_void_rule,operator_sgp_reprice_rule", "S09", "FanDuel help is operator-specific. A universal void/reprice rule is not verified and must not be assumed across books.", "Store the exact operator, jurisdiction, rule version and betslip terms with each quote."),
        ("R12", "Rule-version control", "Overtime and future seasons", "", "S02", "The explicitly extracted overtime change is labeled 2025. The 2026 scoring PDF is separately verified; do not silently apply historical rules to later seasons.", "Pin the effective rulebook version to each season and re-verify before model updates."),
        ("R13", "No live ingestion claim", "Site data freshness", "live_refresh_timestamp", "S10", "This release is a frozen 2026-11-02 research snapshot. The site does not claim live odds, live injuries, or automatic sportsbook execution.", "Treat every refresh as a new evidence snapshot and rerun all gates."),
    ]
    review_items = [dict(id=i, title=t, affected=a, blank_fields=b.split(",") if b else [],
                         source_ids=[s], source_urls=[source[s]["url"]], status="needs review",
                         detail=d, action=act) for i, t, a, b, s, d, act in reviews]
    dump(ROOT / "data" / "own5_desk" / "source_register.json", sources)
    dump(ROOT / "research/official_snapshot.json", snapshot)
    dump(ROOT / "data" / "own5_desk" / "verified_facts.json", facts)
    dump(ROOT / "data" / "own5_desk" / "review_items.json", review_items)
    return dict(sources=len(sources), verified_rows=len(facts), teams=len(teams),
                schedule=len(schedule), paired_games=len(paired), review_items=len(review_items),
                points_reconciliation=snapshot["reconciliation"])


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))

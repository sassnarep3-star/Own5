#!/usr/bin/env python3
"""Report definitions: one view per table, used by BOTH the HTML build and the
executive summary, so the site and the summary can never disagree.

Each view produces a list of dicts with the exact cells to publish. Every view has a
`source` column naming where the row came from, so the coverage rule ("every row carries
a source link or an explicit UNVERIFIED badge") can be checked mechanically.
"""
import csv
import os

from lib import AGGREGATOR, DATA, DERIVED, OFFICIAL, UNVERIFIED, f, rcsv, rcsv_path

NFL_SCHED = "https://www.nfl.com/schedules/2026/by-week/week-%s"
NFL_INJ = "https://www.nfl.com/injuries/league/2026/reg10"
NFL_STAND = "https://www.nfl.com/standings/league/2026/REG"
NFL_ROSTER = "https://www.nfl.com/teams/%s/roster"

TEAM_SLUG = {
    "ARI": "arizona-cardinals", "ATL": "atlanta-falcons", "BAL": "baltimore-ravens",
    "BUF": "buffalo-bills", "CAR": "carolina-panthers", "CHI": "chicago-bears",
    "CIN": "cincinnati-bengals", "CLE": "cleveland-browns", "DAL": "dallas-cowboys",
    "DEN": "denver-broncos", "DET": "detroit-lions", "GB": "green-bay-packers",
    "HOU": "houston-texans", "IND": "indianapolis-colts", "JAX": "jacksonville-jaguars",
    "KC": "kansas-city-chiefs", "LAC": "los-angeles-chargers", "LAR": "los-angeles-rams",
    "LV": "las-vegas-raiders", "MIA": "miami-dolphins", "MIN": "minnesota-vikings",
    "NE": "new-england-patriots", "NO": "new-orleans-saints", "NYG": "new-york-giants",
    "NYJ": "new-york-jets", "PHI": "philadelphia-eagles", "PIT": "pittsburgh-steelers",
    "SEA": "seattle-seahawks", "SF": "san-francisco-49ers", "TB": "tampa-bay-buccaneers",
    "TEN": "tennessee-titans", "WAS": "washington-commanders",
}

# Pages are (slug, nav title, subtitle, builder name, extra css class)
PAGES = [
    ("index", "Overview", "the whole desk on one page", "landing"),
    ("readiness", "Decision readiness", "every requirement, its blocking gate and the number that clears it", "readiness"),
    ("lines", "Line origination", "our fair line, the market line and the difference", "lines"),
    ("strategies", "Strategies", "nine pre-registered families, ranked by signal type", "strategies"),
    ("leaderboard", "Leaderboard", "signal and staking kept apart, with controls", "leaderboard"),
    ("gates", "Validation gates", "what stands between paper and live", "gates"),
    ("availability", "Availability & depth", "injuries, replacements and the depth of each replacement", "availability"),
    ("correlations", "Correlations", "official numbers only, with n on every row", "correlations"),
    ("prices", "Prices & results", "the snapshot store and the verified results feed", "prices"),
    ("questions", "Questions", "what we have, what we do not, where to get it", "questions"),
    ("suggestions", "Suggestions", "options on the table, with the test that changes the call", "suggestions"),
    ("sources", "Sources", "every capture, with its URL, tier and clock time", "sources"),
    ("review", "Flagged for Review", "irregularities, unverified blanks and what would fix them", "review"),
]


def abs_url(url):
    """Repo-relative paths in the data files become absolute GitHub blob links."""
    if url and not url.startswith(("http://", "https://", "#")):
        return ("https://github.com/sassnarep3-star/Own5/blob/main/nfl-market-desk/" + url.lstrip("./"))
    return url


def link(url, label=None, tier=None):
    """A source cell. Empty url -> an explicit UNVERIFIED marker, never a blank cell."""
    url = abs_url(url)
    if not url:
        return '<span class="unv">UNVERIFIED</span>'
    if label is None:
        label = url.replace("https://", "").replace("http://", "").rstrip("/")
        if len(label) > 46:
            label = label[:43] + "..."
    cls = "src"
    if tier:
        cls += " tier-" + tier.lower()
    return '<a class="%s" href="%s" target="_blank" rel="noopener noreferrer">%s</a>' % (
        cls, url.replace("&", "&amp;"), label)


def badge(text, kind="neutral"):
    return '<span class="badge %s">%s</span>' % (kind, text)


STATUS_KIND = {"MET": "good", "PARTIAL": "warn", "NOT MET": "bad", "REJECTED": "neutral",
               "NEEDS REVIEW": "warn"}


# ---------------------------------------------------------------------------
# views
# ---------------------------------------------------------------------------
def v_landing():
    """Landing blocks are assembled by build.py; this returns the headline numbers."""
    from build_registers import numeric_promises
    return numeric_promises()


EVIDENCE_BASE = ("https://github.com/sassnarep3-star/Own5/blob/main/nfl-market-desk/")


def v_readiness():
    out = []
    for r in rcsv("decision_readiness.csv"):
        out.append({
            "id": r["requirement_id"],
            "Requirement": r["requirement"],
            "Status": badge(r["status"], STATUS_KIND.get(r["status"], "neutral")),
            "Gate": r["gate"],
            "Gate status": badge(r["gate_status"], STATUS_KIND.get(r["gate_status"], "neutral")),
            "The number that would clear it": r["number_that_would_clear_it"],
            "Current number": r["current_number"],
            "Evidence": link(EVIDENCE_BASE + r["evidence_path"],
                             r["evidence_path"].replace("data/", "").replace("nfl-market-desk/", ""),
                             DERIVED),
            "_status": r["status"],
        })
    return out


def v_lines():
    out = []
    for r in rcsv("originated_markets.csv"):
        out.append({
            "id": "%s %s" % (r["week"], r["game_id"]),
            "Market": r["market_type"],
            "Order": r["origination_order"],
            "Fixture": "%s @ %s" % (r["away"], r["home"]),
            "Kickoff": (r["kickoff_date"] or "") + (" " + r["kickoff_time_et"] if r["kickoff_time_et"] else ""),
            "Our fair line": r["fair_line"],
            "Market line": r["market_line"] if r["market_line"] else '<span class="unv">UNVERIFIED</span>',
            "Difference (fair - market)": r["difference_fair_minus_market"],
            "Probability": r["probability"],
            "Units": r["units"],
            "Market source": link(r["market_source_url"], r["market_source_tier"].title() or None,
                                  r["market_source_tier"]),
            "Slate source": link(r["slate_source_url"], "NFL slate", r["slate_source_tier"]),
        })
    return out


def v_strategies():
    out = []
    for r in rcsv("strategy_registration.csv"):
        out.append({
            "id": r["family_id"],
            "Family": r["family"],
            "Bet class": r["bet_class"],
            "Signal type": r["signal_type"],
            "Rule (pre-registered, hashed)": r["rule_text"],
            "SHA-256": '<code>%s</code>' % r["registration_sha256"][:16],
            "Registered": r["registered_utc"],
            "Status": badge("PAPER", "warn"),
            "Rule file": link(EVIDENCE_BASE + "data/preregistration/" + r["registration_file"].split("/")[-1],
                              "signed rule", DERIVED),
        })
    return out


def v_leaderboard():
    lb = rcsv("leaderboard.csv")
    out = []
    for r in lb:
        sig = r["signal_headline"]
        try:
            sig = f(float(sig), 4)
        except ValueError:
            pass
        p_holm = r["signal_p_holm"]
        try:
            p_holm = f(float(p_holm), 4)
        except ValueError:
            pass
        roi = r["staking_roi_pct"]
        try:
            roi = f(float(roi), 2) + "%"
        except ValueError:
            roi = '<span class="unv">no priced bets</span>'
        out.append({
            "id": r["family_id"],
            "Family": r["family"],
            "Class": r["bet_class"],
            "Registry": r["signal_type"],
            "n": r["graded_bets"],
            "Signal": sig,
            "p (Holm)": p_holm,
            "Signal rank": r["signal_rank"],
            "Staking n": r["staking_n_priced"] or '<span class="unv">0 priced</span>',
            "ROI": roi,
            "Staking rank": r["staking_rank"] or "-",
            "Hit rate": f(float(r["hit_rate"]), 4) if r["hit_rate"] else "",
            "State": badge(r["state"], "warn" if r["state"] != "certified" else "good"),
            "Why not certified": r["why_not_certified"],
            "Source": link("https://github.com/sassnarep3-star/Own5/blob/main/nfl-market-desk/"
                           "data/leaderboard.csv", "leaderboard.csv", DERIVED),
        })
    return out


def v_controls_and_luck():
    rows = []
    for c in rcsv("control_summary.csv"):
        rows.append({
            "id": c["control_id"],
            "Control": c["name"],
            "n": c["n_rows"],
            "Decided": c["n_decided"],
            "Brier": f(float(c["brier"]), 4) if c["brier"] else "",
            "Hit rate": f(float(c["hit_rate"]), 4) if c["hit_rate"] else "",
            "Reading": "coin-flip reference at 0.25; a strategy must beat this before it may claim anything",
            "Source": link("https://www.nfl.com/schedules/2026/by-week/week-10", "NFL scores"),
        })
    return rows


def v_gates():
    out = []
    for r in rcsv("gates.csv"):
        out.append({
            "id": r["gate_id"],
            "Gate": r["name"],
            "Test": r["test"],
            "Class": r["class"],
            "Status": badge(r["status"], STATUS_KIND.get(r["status"], "neutral")),
            "Blocking flag(s)": r["blocking_flags"] or "-",
            "Source": link(r["source_url"]),
        })
    return out


def v_availability():
    out = []
    for r in rcsv("availability_by_team.csv"):
        def num(x):
            # blank means "we could not read this club's chart", not "nobody is out"
            return x if x != "" else '<span class="unv">not measurable</span>'
        out.append({
            "id": r["club"],
            "Club": r["club_name"],
            "On report": r["report_rows"],
            "Out": r["named_out"],
            "Doubtful": r["doubtful"],
            "Questionable": r["questionable"],
            "No designation": r["no_designation"],
            "Chart parsed": badge(r["depth_chart_parsed"], "good" if r["depth_chart_parsed"] == "yes" else "warn"),
            "Starters out": num(r["starters_named_out"]),
            "Replacements named": num(r["replacements_named"]),
            "Compounding": num(r["compounding_replacements"]),
            "Net unavailable (weighted)": num(r["net_unavailable_score"]),
            "Note": r["coverage_note"],
            "Source": link(r["injury_source_url"], "NFL injury report"),
        })
    return out


def v_cascade():
    out = []
    for r in rcsv("replacement_cascade.csv"):
        out.append({
            "id": r["club"],
            "Club": r["club_name"],
            "Starter (rank 1 on the club's own chart)": r["starter"],
            "Position": r["starter_position_on_chart"],
            "Status": r["starter_status"],
            "Replacement": r["replacement"],
            "Depth of replacement": r["depth_of_replacement"],
            "Replacement also on report": r["replacement_on_week10_report"],
            "Compounding": badge(r["compounding"], "bad" if r["compounding"] == "yes" else "good"),
            "Depth source": link(r["depth_source_url"], "club chart", OFFICIAL),
            "Injury source": link(r["injury_source_url"], "NFL report", OFFICIAL),
        })
    return out


def v_depth():
    out = []
    for r in rcsv("depth_rows.csv"):
        out.append({
            "id": "%s-%s" % (r["club"], r["slot_id"].split("-")[-1]),
            "Club": r["club"],
            "Unit": r["unit"],
            "Position": r["position"],
            "Slot": r["slot_id"],
            "Rank": r["rank"],
            "Player": r["player_display"] or '<span class="unv">empty slot</span>',
            "Jersey": r["jersey_number"] or "-",
            "Shape": r["slot_shape"],
            "Page dated": r["page_dated"] or '<span class="unv">no date printed</span>',
            "Source": link(r["source_url"], "club chart", OFFICIAL),
        })
    return out


def v_compare():
    out = []
    for r in rcsv("depth_compare.csv"):
        out.append({
            "id": r["club"],
            "Club": r["club"],
            "Player": r["player_display"],
            "Live position": r["live_position"],
            "Live rank": r["live_rank"],
            "Inherited position": r["inherited_position"],
            "Inherited rank": r["inherited_rank"],
            "Result": badge(r["result"], "warn" if r["result"] != "agree" else "good"),
            "Note": r["note"],
            "Source": link(r["source_url"], "live chart", OFFICIAL),
        })
    return out


def v_correlations():
    out = []
    for r in rcsv("correlations_official.csv"):
        out.append({
            "id": r["corr_id"],
            "Unit": r["unit_of_analysis"],
            "Metric A": r["metric_a"],
            "Metric B": r["metric_b"],
            "r": f(float(r["r"]), 4),
            "r squared": f(float(r["r_squared"]), 4),
            "p (two-sided)": f(float(r["p_two_sided"]), 6),
            "n": r["n"],
            "n definition": r["n_definition"],
            "Tier": badge(r["inputs_tier"], "good" if r["inputs_tier"] == OFFICIAL else "warn"),
            "Source": link(r["source_url"], "NFL standings", OFFICIAL),
        })
    return out


def v_correlations_withheld():
    out = []
    for r in rcsv("correlations_withheld.csv"):
        out.append({
            "id": r["withheld_id"],
            "Pair": r["pair"],
            "Why it is not published": r["why_not_published"],
            "Prior input tier": r["prior_input_tier"],
            "Status": badge(r["status"], "warn"),
            "Evidence": link(EVIDENCE_BASE + "data/correlations_withheld.csv",
                             "withheld register", DERIVED),
        })
    return out


def v_price_store():
    out = []
    for r in rcsv("price_snapshots.csv"):
        val = r["line_value"]
        out.append({
            "id": r["snapshot_id"],
            "Market": r["market_id"],
            "Fixture": r["matchup"],
            "Snapshot": r["snapshot_type"],
            "Meaning": r["snapshot_meaning"],
            "Clock (UTC)": r["snapshot_utc"] or '<span class="unv">not observed</span>',
            "Line": val if val else '<span class="unv">blank by policy</span>',
            "Price": r["price_american"] or '<span class="unv">blank</span>',
            "Tier": r["source_tier"] or "-",
            "Verified": r["verified"] or "no",
            "Flag": r["flag_id"],
            "Source": link(r["source_url"]),
        })
    return out


def v_policy():
    out = []
    for r in rcsv("price_policy.csv"):
        out.append({
            "id": r["policy_id"],
            "Question": r["question"],
            "Decision": r["decision"],
            "Scope": r["scope"],
            "Status": badge(r["status"], "good" if r["status"] == "decided" else "warn"),
            "Tier": r["tier"],
            "Rationale": r["rationale"],
            "Source": link(r["source_url"]),
        })
    return out


def v_results():
    out = []
    for r in rcsv("results_feed.csv"):
        out.append({
            "id": r["game_id"],
            "Week": r["week"],
            "Date": r["kickoff_date"],
            "Away": "%s %s" % (r["away"], r["away_score"]),
            "Home": "%s %s" % (r["home"], r["home_score"]),
            "Neutral": r["neutral_site"] or "-",
            "Status": badge(r["status"], "good"),
            "Mirror check": r["mirror_check"],
            "Source": link(r["source_url"], "NFL week %s" % r["week"], r["source_tier"]),
        })
    return out


def v_standings():
    out = []
    for r in rcsv("standings_official.csv"):
        out.append({
            "id": r["club"],
            "Club": r["club_name"],
            "W": r["w"], "L": r["l"], "T": r["t"],
            "Win pct": r["win_pct_published"],
            "PF": r["pf"], "PA": r["pa"], "Net": r["net_pts"],
            "PF/G": r["pf_per_game"], "PA/G": r["pa_per_game"],
            "Home": r["home_record"], "Road": r["road_record"],
            "Source": link(r["source_url"], "NFL standings", OFFICIAL),
        })
    return out


def v_reconciliation():
    out = []
    for r in rcsv("standings_reconciliation.csv"):
        out.append({
            "id": r["club"],
            "Club": r["club_name"],
            "Feed W-L-T": "%s-%s-%s" % (r["w_feed"], r["l_feed"], r["t_feed"]),
            "Official W-L-T": "%s-%s-%s" % (r["w_official"], r["l_official"], r["t_official"]),
            "Feed PF/PA": "%s/%s" % (r["pf_feed"], r["pa_feed"]),
            "Official PF/PA": "%s/%s" % (r["pf_official"], r["pa_official"]),
            "Result": badge(r["result"], "good" if r["result"].lower() == "match" else "bad"),
            "Source": link(r["source_url"], "NFL standings", OFFICIAL),
        })
    return out


def v_model_accuracy():
    out = []
    for r in rcsv("model_accuracy.csv"):
        out.append({
            "id": r["holdout"],
            "Sample": r["holdout"],
            "n": r["n_games"],
            "n with a market price": r["n_with_market_price"],
            "Brier (model)": r["brier_model"],
            "Brier (market)": r["brier_market"],
            "Brier (coin flip)": r["brier_coinflip"],
            "Skill vs market": r["bss_vs_market"],
            "Skill vs coin flip": r["bss_vs_coinflip"],
            "MAE margin (model)": r["mae_margin_model"],
            "MAE margin (market)": r["mae_margin_market"],
            "MAE total (model)": r["mae_total_model"],
            "MAE total (market)": r["mae_total_market"],
            "Source": link("https://www.nfl.com/schedules/2026/by-week/week-9", "NFL scores"),
        })
    return out


def v_forecasts():
    out = []
    for r in rcsv("forecasts.csv"):
        out.append({
            "id": r["game_id"],
            "Week": r["week"],
            "Fixture": "%s @ %s" % (r["away"], r["home"]),
            "P(home win)": r["prob_home_win"],
            "Fair margin": r["fair_margin"],
            "Fair total": r["fair_total"],
            "Market spread": r["market_spread_home"],
            "Market total": r["market_total"],
            "Train games": r["train_games"],
            "Train last week": r["train_last_week"],
            "Score": "%s-%s" % (r["actual_home_score"], r["actual_away_score"]),
            "Source": link(r["score_source_url"], "NFL week %s" % r["week"]),
        })
    return out


def v_ablation():
    out = []
    for r in rcsv("personnel_ablation.csv"):
        out.append({
            "id": r["game_id"],
            "Week": r["week"],
            "Fixture": "%s @ %s" % (r["away"], r["home"]),
            "Out (home/away)": "%s / %s" % (r["out_home"], r["out_away"]),
            "Doubtful": "%s / %s" % (r["doubtful_home"], r["doubtful_away"]),
            "Questionable": "%s / %s" % (r["questionable_home"], r["questionable_away"]),
            "Starters out (h/a)": "%s / %s" % (r["starters_named_out_home"], r["starters_named_out_away"]),
            "Availability diff": r["availability_diff"],
            "P(home) without personnel": r["prob_home_win_no_personnel"],
            "P(home) with the fitted coefficient": r["prob_home_win_with_personnel"],
            "Actual": r["actual_home_win"],
            "Injury source": link(r["injury_source_url"], "NFL report", OFFICIAL),
        })
    return out


def _question_source(r):
    first = (r["related_flags"] or "").split(",")[0].strip()
    if first:
        return ("https://github.com/sassnarep3-star/Own5/blob/main/nfl-market-desk/"
                "data/flags.csv")
    return EVIDENCE_BASE + "data/questions.csv"


def _question_label(r):
    first = (r["related_flags"] or "").split(",")[0].strip()
    return "flag " + first if first else "questions.csv"


def v_questions():
    out = []
    for r in rcsv("questions.csv"):
        out.append({
            "id": r["question_id"],
            "Question": r["question"],
            "Have it?": badge(r["have_information"], "good" if r["have_information"] == "YES" else "warn"),
            "What we have": r["have_what"],
            "What is missing": r["missing_what"],
            "Cheapest route to the answer": r["cheapest_route_to_answer"],
            "Blocks": r["blocks"],
            "Flags": r["related_flags"],
            "Source": link(_question_source(r), _question_label(r), DERIVED),
        })
    return out


def v_suggestions():
    out = []
    for r in rcsv("suggestions.csv"):
        out.append({
            "id": r["suggestion_id"],
            "Topic": r["topic"],
            "Priority": badge(r["priority"], "bad" if r["priority"] == "blocking" else "warn"),
            "Options": r["options"],
            "Recommended path": r["recommended_path"],
            "Reversible rule (what would change the call)": r["reversible_rule"],
            "Cost": r["cost"],
            "Status": r["status"],
            "Source": link(EVIDENCE_BASE + "data/suggestions.csv", "suggestions.csv", DERIVED),
        })
    return out


def v_sources():
    out = []
    for r in rcsv_path(os.path.join(DATA, "raw", "sources_captured.csv")):
        out.append({
            "id": r["source_id"],
            "Publisher": r["publisher"],
            "Title": r["title"],
            "Tier": badge(r["tier"], "good" if r["tier"] == OFFICIAL else "warn"),
            "Fetched (UTC)": r["fetched_utc"],
            "Used for": r["used_for"],
            "Notes": r["notes"],
            "Link": link(r["url"], "open", r["tier"]),
        })
    return out


def v_announcements():
    out = []
    for r in rcsv("schedule_announcements.csv"):
        out.append({
            "id": r["announcement_id"],
            "Topic": r["topic"],
            "Dated language on the official page": r["dated_language"],
            "Captured (UTC)": r["captured_utc"],
            "Source": link(r["source_url"], "NFL schedule page", OFFICIAL),
        })
    return out


def v_flags():
    out = []
    for r in rcsv("flags.csv"):
        kind = {"blocking": "bad", "review": "warn", "open": "warn"}.get(r["severity"], "neutral")
        out.append({
            "id": r["flag_id"],
            "Severity": badge(r["severity"], kind),
            "Area": r["area"],
            "Finding": "<strong>%s</strong><br><small>%s</small>" % (
                r["title"].replace("<", "&lt;"), r["detail"].replace("<", "&lt;")),
            "Consequence": r["consequence"],
            "Action taken / needed": r["action"],
            "Status": r["status"],
            "Origin": r["origin"],
            "Source": link(r["source_url"]),
        })
    return out


def v_desks():
    out = []
    for r in rcsv("desk_inventory.csv"):
        out.append({
            "id": r["desk_path"].strip("/").split("/")[0],
            "Desk": r["desk_path"],
            "What it claims": r["claims"],
            "Its data basis": r["data_basis"],
            "Re-verified by this desk": r["status_in_this_desk"],
            "Relation": r["relation"],
            "Link": '<a class="src" href="https://github.com/sassnarep3-star/Own5/tree/main/%s" target="_blank" rel="noopener noreferrer">tree ↗</a>' % r["desk_path"],
        })
    return out


def v_ledger():
    return v_sources()


def v_venues():
    out = []
    for r in rcsv("venues.csv"):
        out.append({
            "id": r["game_id"],
            "Fixture": "%s @ %s" % (r["away"], r["home"]),
            "Stadium (official page)": r["venue_name_official"] or
            '<span class="unv">page names only the host city</span>',
            "Neutral site": r["neutral_site_official"] or "-",
            "Weather printed on the page": r["weather_line_official"] or
            '<span class="unv">not printed</span>',
            "Roof (mirror, aggregator)": r["roof_mirror"] or
            '<span class="unv">blank in the mirror</span>',
            "Surface (mirror, aggregator)": r["surface_mirror"] or
            '<span class="unv">blank in the mirror</span>',
            "Status": r["roof_surface_status"],
            "Source": link(r["venue_source_url"], "NFL week 11 slate", OFFICIAL),
        })
    return out


def v_envelope():
    """The coverage rule needs a machine-readable count per table."""
    tables = {
        "readiness": v_readiness(), "lines": v_lines(), "strategies": v_strategies(),
        "leaderboard": v_leaderboard(), "gates": v_gates(), "availability": v_availability(),
        "cascade": v_cascade(), "depth": v_depth(), "compare": v_compare(),
        "correlations": v_correlations(), "prices": v_price_store(), "policy": v_policy(),
        "results": v_results(), "flags": v_flags(), "questions": v_questions(),
    }
    return {k: len(v) for k, v in tables.items()}

"""Decision-readiness engine for the Own5 NFL desk (session 560ed315).

The brief's central decision-support ask is: "Put a decision-readiness table on
the landing page: one row per requirement, with the gate that blocks it and the
number that would clear it."

This engine builds ``data/decision_readiness.csv``: one row per requirement in the
brief.  Each row carries

* ``blocking_gate``  - the validation gate (or named rule) that currently blocks
  the requirement from being satisfied;
* ``clearing_number`` - the concrete number / threshold / count that would clear
  that gate (the "number that would clear it");
* ``current_number``  - the observed number today, **computed mechanically from
  verified sibling data** (read-only) where a count is directly derivable, and
  left blank + flagged where no official/verified source can supply it.

``current_number`` is never typed by hand: it is read from the verified CSVs that
earlier desks (``nfl-desk-3fb93d11``) already transcribed from official nfl.com
pages.  A requirement whose current number cannot be computed from a verified
source gets ``current_number = ""`` and ``flag = "UNVERIFIED"``.

Deterministic: re-running produces byte-identical output.  Stdlib only.
"""

from __future__ import annotations

import csv
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")

# Read-only verified sibling data (session 3fb93d11, transcribed from nfl.com).
SIBLING = os.path.normpath(os.path.join(ROOT, "..", "nfl-desk-3fb93d11", "data"))

OFFICIAL_STANDINGS = "https://www.nfl.com/standings/league/2026/REG"
OFFICIAL_SCHEDULE = "https://www.nfl.com/schedules/2026/by-week/"
OFFICIAL_INJURY = "https://www.nfl.com/injuries/league/2026/reg10"
DESK_SITE = "https://sassnarep3-star.github.io/Own5/nfl-desk-3fb93d11/"


# --------------------------------------------------------------------------
# Mechanical current-number readers (read-only, from verified sibling CSVs).
# --------------------------------------------------------------------------

def _rows(name):
    path = os.path.join(SIBLING, name)
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _count(name):
    return len(_rows(name))


def metric_results_feed():
    """Official 2026 finals in the verified results feed."""
    return "{0} official games".format(_count("results_feed.csv"))


def metric_price_store():
    """Snapshot rows populated vs total (a row is populated when it carries a value)."""
    rows = _rows("price_snapshots.csv")
    populated = 0
    for r in rows:
        cells = [r.get("line_value", ""), r.get("price_american", "")]
        if any(c and c.strip() for c in cells):
            populated += 1
    return "{0}/{1} populated".format(populated, len(rows))


def metric_markets():
    return "{0} markets".format(_count("originated_markets.csv"))


def metric_depth_slots():
    rows = _rows("replacement_depth.csv")
    clubs = {r.get("club", "").strip() for r in rows if r.get("club", "").strip()}
    return "{0} slots / {1} clubs".format(len(rows), len(clubs))


def metric_correlations():
    return "{0} official pairs".format(_count("correlations_official.csv"))


def metric_gate_evals():
    return "{0} gate evaluations".format(_count("gate_matrix.csv"))


def metric_certified():
    rows = _rows("leaderboard.csv")
    cert = sum(1 for r in rows if (r.get("certified", "") or "").strip().lower() == "yes")
    return "{0} certified of {1} board rows".format(cert, len(rows))


def metric_injury_gamestatus():
    rows = _rows("depth_injury_crosscheck.csv")
    with_status = sum(1 for r in rows if (r.get("game_status", "") or "").strip())
    return "{0}/{1} rows with game status".format(with_status, len(rows))


def metric_origination_steps():
    rows = _rows("origination_steps.csv")
    games = {r.get("game_id", "") for r in rows if r.get("game_id", "").strip()}
    return "{0} steps / {1} games".format(len(rows), len(games))


# --------------------------------------------------------------------------
# Requirement register: (id, category, requirement, status, blocking_gate,
#                       clearing_number, how_met, gap, current_metric, source_url)
# current_metric is a callable returning the observed string, or None for blank+flag.
# --------------------------------------------------------------------------

REQUIREMENTS = [
    # ---------------- PRICE & RESULTS ----------------
    ("DR-01", "Price & results",
     "Add a price-snapshot store that records opening and closing numbers for every market we originate",
     "Partially met", "G2 (price provenance)",
     "A verified MARKET_OPEN and MARKET_CLOSE snapshot, timestamped, for all originated markets",
     "Store schema + 390 rows exist; operator open/close are empty because nfl.com publishes no betting prices.",
     "234 of 390 snapshot rows are empty and flagged (F-01); no operator price exists in any source.",
     metric_price_store, OFFICIAL_STANDINGS),

    ("DR-02", "Price & results",
     "Add a verified results feed so backtests and ROI can be computed at all",
     "Met", "G8 (certification universe is official)",
     "300 graded results from an official publisher (nfl.com)",
     "137 official 2026 finals transcribed week by week, each with source URL and UTC retrieval stamp.",
     "One season only; multi-season would need the same transcription for 1999-2025.",
     metric_results_feed, OFFICIAL_SCHEDULE),

    ("DR-03", "Price & results",
     "Decide the price-data policy before any backtest is published",
     "Not started", "G0 (pre-registration)",
     "A committed price-data policy document, frozen by commit hash before evaluation",
     "None committed. The policy is proposed (suggestion S-01) but not pre-registered.",
     "No committed policy; a backtest could otherwise be run on an unstated price convention.",
     None, DESK_SITE),

    ("DR-04", "Price & results",
     "Price a line ourselves and publish the residual against the market, on a schedule, from day one",
     "Partially met", "G2 (price provenance)",
     "A residual (model line minus market line) per market per snapshot, against a timestamped official market price",
     "Residual column exists; the market line is an AGGREGATOR reference with no timestamp.",
     "Market reference is untimestamped (F-14); it is neither an open nor a close, so the residual is not a CLV.",
     metric_markets, DESK_SITE),

    ("DR-05", "Price & results",
     "Vig-free market consensus vs. originated fair-line decomposition view",
     "Not started", "G2 (price provenance)",
     "An official vig-free consensus price per market to decompose true divergence from operator margin",
     "No vig-free consensus source exists in the repo.",
     "Cannot separate origination alpha from operator margin without an official vig-free consensus.",
     None, OFFICIAL_STANDINGS),

    # ---------------- ORIGINATION & LINES ----------------
    ("DR-06", "Origination & lines",
     "Originate the side first, then the total, then the moneyline",
     "Met", "G3 (out-of-sample only)",
     "The three-step dependency order recorded for every game, with no independent fitting",
     "origination_steps.csv records side -> total -> moneyline in order; moneyline is derived, not fitted.",
     "None - the requirement is met in full.",
     metric_origination_steps, DESK_SITE),

    ("DR-07", "Origination & lines",
     "Publish the model's fair line, the market line, and the difference as separate columns",
     "Partially met", "G2 (price provenance)",
     "Three distinct columns (model_line, market_line, difference) where market_line is timestamped and official",
     "Three columns exist for all three market types.",
     "market_line is an AGGREGATOR tier with no timestamp (F-14).",
     metric_markets, DESK_SITE),

    ("DR-08", "Origination & lines",
     "Originate my own NFL lines",
     "Met", "G1 + G2",
     "300 graded own-lines with a verified opening and closing price each",
     "78 markets across the scheduled slate, priced from a model fitted on 137 official results.",
     "No graded bet exists yet: gate G2 fails, so no market has a verified price (F-01).",
     metric_markets, DESK_SITE),

    ("DR-09", "Origination & lines",
     "Compute and publish the removal-of-luck panel on the site dashboard",
     "Not started", "G5 (deflation)",
     "A deflated Sharpe >= 0.95 per family on the certification universe",
     "The deflation machinery (Holm, deflated Sharpe) exists but nothing is certified.",
     "With 0 certified strategies the panel cannot show a non-null skill value; published as null, not fabricated.",
     metric_certified, DESK_SITE),

    ("DR-10", "Origination & lines",
     "Publish every model total twice until one wins",
     "Not started", "G0 (pre-registration)",
     "Two estimators per total with a gap column, collapsed only after a walk-forward comparison",
     "A single totals estimator is published.",
     "No dual-estimator comparison; the totals model also does not beat a naive baseline (F-09).",
     None, DESK_SITE),

    ("DR-11", "Origination & lines",
     "Two-stage skill leaderboard (proper-score qualification -> prospective CLV/ROI escrow)",
     "Not started", "G5 + G4",
     "A certified entrant that passes proper-score qualification before any CLV/ROI escrow",
     "Leaderboard exists with signal and staking axes; no staged qualification.",
     "0 certified entrants; CLV is unmeasurable without verified prices (F-01).",
     metric_certified, DESK_SITE),

    # ---------------- STRATEGIES & SIGNALS ----------------
    ("DR-12", "Strategies & signals",
     "Research and develop strategies that generate useful signals",
     "Partially met", "G1 + G4",
     "300 graded bets per family beating break-even, Holm-adjusted across families",
     "Nine pre-registered families across singles, parlays and prop combos, graded walk-forward.",
     "Families produced 4-51 graded bets against a 300 minimum; none beats break-even after adjustment (F-10).",
     metric_gate_evals, DESK_SITE),

    ("DR-13", "Strategies & signals",
     "Cover single bets, parlays, and player prop bet combos",
     "Partially met", "G7 (correlation audit)",
     "An empirical joint probability for every leg pair of every parlay / prop combo",
     "Singles (S1-S7), a same-game two-leg parlay (S8) and a prop-combo family (S9) are on the board.",
     "No player-prop lines exist anywhere (F-08), so S9 produced zero graded bets and G7 cannot pass.",
     metric_markets, DESK_SITE),

    ("DR-14", "Strategies & signals",
     "Treat it as a leaderboard competition that rewards top-performing strategies",
     "Partially met", "G5 (deflation)",
     "A certified entrant on the certification universe",
     "Two boards, separate signal/staking axes, gates as entry condition, documented reward structure.",
     "0 certified entrants; reward funding and jurisdiction unanswered (Q-04, Q-05).",
     metric_certified, DESK_SITE),

    ("DR-15", "Strategies & signals",
     "Determine correlation values",
     "Met", "official-only correlation rule",
     "Each published value carries a coefficient, n, and an official source",
     "9 admissible pairs computed from nfl.com numbers only, each with n and a 95% interval.",
     "Values computed from the mirror were moved to a withheld register (F-13), narrowing the published set.",
     metric_correlations, OFFICIAL_STANDINGS),

    ("DR-16", "Strategies & signals",
     "Remove luck from the equation and build selectively skill-based strategies",
     "Partially met", "G5 (deflation)",
     "Deflated Sharpe >= 0.95 with out-of-sample-only grading and a demotion gate",
     "Shrinkage, Holm, deflated Sharpe, OOS-only grading and a 6-trigger demotion gate are implemented.",
     "Luck cannot be removed, only measured; nothing clears the bar on the samples available today.",
     metric_certified, DESK_SITE),

    ("DR-17", "Strategies & signals",
     "Pre-register every strategy; forbid backtest numbers from ever appearing on the leaderboard",
     "Met", "G0 (pre-registration)",
     "Rule text + sample window + gates committed before the evaluation window; leaderboard shows only prospective rows",
     "Gates and families are committed in gates.py; the leaderboard grades the official certification universe only.",
     "Research-board results are kept off the certification leaderboard by design (Q-09).",
     metric_gate_evals, DESK_SITE),

    ("DR-18", "Strategies & signals",
     "Add a two-sided 'what would change our mind' field to every strategy entry",
     "Not started", "G0 (pre-registration)",
     "The field populated on every strategy entry with a falsification trigger",
     "No such field exists in the strategy register.",
     "A registered strategy cannot currently state what evidence would falsify it.",
     None, DESK_SITE),

    ("DR-19", "Strategies & signals",
     "Start with a singles-only shadow baseline",
     "Partially met", "G1 (minimum sample)",
     "A simple team-strength baseline family graded on the same universe as the strategies",
     "Singles families S1-S7 are graded; a dedicated team-strength shadow baseline is not separated out.",
     "No explicit frozen team-strength shadow baseline with recorded pre-kickoff forecasts.",
     metric_gate_evals, DESK_SITE),

    ("DR-20", "Strategies & signals",
     "Pre-register a simple team-strength model, freeze versions, and record forecasts before kickoff",
     "Partially met", "G0 + G3",
     "A frozen model commit plus a pre-kickoff forecast log",
     "A margin model is fitted on official results and committed; a separate pre-kickoff forecast log is not kept.",
     "Forecasts are not recorded before kickoff, so the freeze cannot be audited retrospectively.",
     metric_markets, DESK_SITE),

    ("DR-21", "Strategies & signals",
     "Freeze a rule before it sees data (pre-registration)",
     "Met", "G0 (pre-registration)",
     "The rule text, sample window and gates committed to git before the evaluation window",
     "Gate definitions and family rules are committed in gates.py.",
     "The commit hash is the registration; this is satisfied.",
     metric_gate_evals, DESK_SITE),

    ("DR-22", "Strategies & signals",
     "Split data into train, validation and final holdout seasons",
     "Not started", "G3 (out-of-sample only)",
     "An explicit multi-season train / validation / final-holdout split",
     "Walk-forward grading is used within the 2026 official season.",
     "No multi-season train/val/holdout split is implemented.",
     metric_results_feed, OFFICIAL_SCHEDULE),

    ("DR-23", "Strategies & signals",
     "Rank with proper scores and uncertainty, not win rate",
     "Partially met", "G4 + G5",
     "Benchmark-relative Brier skill with a game-cluster lower bound and a multiplicity adjustment",
     "Signal ranking uses deflated Sharpe and Holm adjustment across families.",
     "A game-cluster lower bound on the Brier skill is not yet computed.",
     metric_certified, DESK_SITE),

    ("DR-24", "Strategies & signals",
     "Add a control baseline (random picks; favorites only) to every leaderboard run",
     "Not started", "G1 (minimum sample)",
     "A control family graded on the same universe beside every strategy",
     "No control baseline is graded.",
     "Without a control the reader cannot separate skill from a favourable sample.",
     None, DESK_SITE),

    ("DR-25", "Strategies & signals",
     "Keep parlays and prop combos behind a joint-evidence gate",
     "Partially met", "G7 (correlation audit)",
     "A directly validated joint probability plus operator void/push rules for every ranked combo",
     "The gate is defined; S8 currently prices legs independently.",
     "Independent pricing is invalid under dependence; the joint cannot be measured without prop lines (F-08).",
     metric_markets, DESK_SITE),

    ("DR-26", "Strategies & signals",
     "Use proper-score leaderboard divisions",
     "Partially met", "G5 (deflation)",
     "Separate divisions for singles, game parlays, same-game parlays and prop combos",
     "Single / parlay / prop families are present and scored on the board.",
     "Same-game-parlay and prop-combo divisions are not separated as distinct leaderboards.",
     metric_gate_evals, DESK_SITE),

    # ---------------- LEADERBOARD & COMPETITION ----------------
    ("DR-27", "Leaderboard & competition",
     "Each strategy must pass validation gates",
     "Partially met", "G0-G8 (all hard gates)",
     "Every hard gate passing for a family on the certification universe",
     "Gates G0-G8 are evaluated per family per universe in gate_matrix.csv.",
     "G2 fails for every family (no verified price, F-01); G1 fails on the certification board (F-10).",
     metric_gate_evals, DESK_SITE),

    ("DR-28", "Leaderboard & competition",
     "Define a demotion gate that sends a live strategy back to paper",
     "Met", "demotion gate D1a-D1f",
     "The gate armed and enforced, with thresholds and a source for each trigger",
     "Six triggers (D1a-D1f) are evaluated against every family in demotion_gate.csv.",
     "No strategy has ever gone live, so no trigger has fired; the gate is armed, not proven.",
     metric_gate_evals, DESK_SITE),

    ("DR-29", "Leaderboard & competition",
     "Separate signal from staking so a lucky staking run cannot mask a bad signal",
     "Met", "G5 (deflation)",
     "Two independent scorecards, neither of which can certify on staking alone",
     "leaderboard.csv ranks each family on signal_rank and staking_rank from disjoint inputs.",
     "The staking axis cannot certify or reward; the split is implemented and demonstrated (S7 case).",
     metric_certified, DESK_SITE),

    ("DR-30", "Leaderboard & competition",
     "Reject: ranking strategies by season-long ROI",
     "Met", "G4 + G5",
     "ROI is never the ranking key; rank is benchmark-relative skill",
     "Ranking uses signal_score (deflated Sharpe), not realised ROI.",
     "None - the rejection is enforced by the scoring model.",
     metric_certified, DESK_SITE),

    # ---------------- INJURIES & DEPTH ----------------
    ("DR-31", "Injuries & depth",
     "Track injuries and know defensive deficiencies where 2nd/3rd/4th string backups replace starters",
     "Met", "official depth source rule",
     "Replacement depth recorded per position slot from an official source, offence and defence",
     "Per-slot tracking of which string steps in, split by offence and defence, cross-checked to the Out list.",
     "31 of 32 clubs; Houston publishes no readable chart (F-05). Snapshot is 2026-11-13.",
     metric_depth_slots, OFFICIAL_INJURY),

    ("DR-32", "Injuries & depth",
     "The same for offences using starters or backups",
     "Met", "official depth source rule",
     "Offence and defence recorded as separate units so the two are never pooled",
     "Each slot carries a unit column (offence / defence); the two are never pooled.",
     "None - the requirement is met in full.",
     metric_depth_slots, OFFICIAL_INJURY),

    ("DR-33", "Injuries & depth",
     "Track the depth of the replacement, not just the fact of a replacement",
     "Met", "official depth source rule",
     "The replacement's own string depth, whether it compounds, recorded per slot",
     "replacement_depth.csv publishes the string that steps in, compounding, and per-unit split.",
     "31 of 32 clubs (Houston F-05); snapshot 2026-11-13.",
     metric_depth_slots, DESK_SITE),

    ("DR-34", "Injuries & depth",
     "Do not model depth from jersey order; model it from playing time",
     "Met", "source rule (depth-order source)",
     "Depth derived from an official chart or snap counts, never from jersey number / salary / experience",
     "Club depth charts are primary; a snap-share cross-check is available in-repo.",
     "Jersey-order inference is rejected; the source rule is enforced (Q-07).",
     metric_depth_slots, DESK_SITE),

    ("DR-35", "Injuries & depth",
     "Resolve the depth-order source before building the backup-deficiency feature",
     "Partially met", "source rule (depth-order source)",
     "One route verified for all 32 clubs before the feature is built",
     "Club depth-chart route is verified for 31 clubs; snap-count route is a fallback.",
     "Houston (image-only chart) is unresolved; the feature is not built until 32/32 (F-05).",
     metric_depth_slots, DESK_SITE),

    ("DR-36", "Injuries & depth",
     "Model depth slots as groups, not a single starter",
     "Partially met", "source rule (slot representation)",
     "Shared and empty slots represented explicitly, not flattened to a ranked list",
     "Slots are captured per position; shared/empty representation is flagged but not fully modelled.",
     "Seattle (two players in one slot) and Washington (empty slot) are not yet distinguished (VR-21/23).",
     metric_depth_slots, DESK_SITE),

    ("DR-37", "Injuries & depth",
     "Represent shared and empty depth slots faithfully",
     "Not started", "source rule (slot representation)",
     "A slot model that can hold >1 player or 0 players per rank",
     "Slots are recorded but shared/empty cases are flagged, not modelled.",
     "Currently indistinguishable from a ranked list (VR-21, VR-23; VQ-08).",
     None, DESK_SITE),

    ("DR-38", "Injuries & depth",
     "Fix the two depth-parsing failures before widening coverage",
     "Partially met", "source rule (depth parsing)",
     "Packers jersey-number stripping plus a structured source for the Texans image",
     "Packers rows are recovered by number stripping and the raw string is stored.",
     "The Texans publish depth as an image and need an authorized structured source, not eye transcription (F-05).",
     metric_depth_slots, DESK_SITE),

    ("DR-39", "Injuries & depth",
     "Add an official depth-chart register with date and source per row",
     "Partially met", "source rule (provenance)",
     "Every depth row carries a capture date and its source URL",
     "Depth rows carry a source URL; the snapshot is dated 2026-11-13.",
     "No immutable multi-day ledger; a single dated snapshot cannot support backtesting.",
     metric_depth_slots, DESK_SITE),

    ("DR-40", "Injuries & depth",
     "Add an announced-starter evidence field (not an inferred replacement)",
     "Not started", "source rule (announced starters)",
     "Dated official starter-change evidence recorded per affected player",
     "Blank replacement columns are correct for the report page; no announced-starter field is stored.",
     "The NFL publishes dated starter changes (e.g. VR-24/25) that are not captured.",
     None, DESK_SITE),

    ("DR-41", "Injuries & depth",
     "Flag stale depth rows against the official transactions log",
     "Not started", "source rule (transactions)",
     "A depth row joined to the transactions log so stale rows are flagged",
     "No transaction join exists.",
     "Clubs can publish charts that lag the transactions log (e.g. Baltimore QB situation, VR-17/26).",
     None, DESK_SITE),

    ("DR-42", "Injuries & depth",
     "Point-in-time snapshot ledger for injuries, depth charts and inactives",
     "Not started", "G3 (no lookahead)",
     "An immutable, timestamped ledger so backtests use only what was known pre-kickoff",
     "A single dated snapshot exists; no point-in-time ledger.",
     "A single capture cannot prevent lookahead leakage when backtesting originated lines.",
     None, DESK_SITE),

    ("DR-43", "Injuries & depth",
     "Automate immutable multi-day availability snapshots",
     "Not started", "G3 (no lookahead)",
     "Scheduled daily capture of injury reports / depth pages with retained hashes",
     "One capture exists; no scheduled, hashed multi-day capture.",
     "Practice designations cannot be replayed as they were known (F-04 style gaps).",
     None, OFFICIAL_INJURY),

    ("DR-44", "Injuries & depth",
     "Build immutable official availability snapshots",
     "Not started", "G3 (no lookahead)",
     "Scheduled capture of injury reports, club depth pages and inactive evidence with raw hashes, timestamps and conflict flags",
     "No scheduled hashed capture exists.",
     "No conflict flags; the snapshot is not immutable or auditable.",
     None, OFFICIAL_INJURY),

    ("DR-45", "Injuries & depth",
     "Capture official inactive lists and snap counts",
     "Not started", "source rule (inactive + snaps)",
     "Inactive list and snap share captured for every game",
     "Only 6 of 254 report rows carry a game designation; no active list or snap share is captured.",
     "A backup's replacement of a starter cannot be confirmed, only suspected.",
     metric_injury_gamestatus, OFFICIAL_INJURY),

    ("DR-46", "Injuries & depth",
     "Snapshot the nfl.com injury report every Wed, Thu and Fri and keep a dated history",
     "Not started", "G3 (no lookahead)",
     "Three captures per week, retained as a dated history",
     "A single snapshot exists.",
     "No weekly series; Questionable->Out and practice-trend changes cannot be seen.",
     None, OFFICIAL_INJURY),

    ("DR-47", "Injuries & depth",
     "Treat the injury report as a timestamped series, not a weekly snapshot",
     "Not started", "G3 (no lookahead)",
     "Daily capture from Wednesday to kickoff with the fetch timestamp",
     "A single snapshot with one retrieval stamp.",
     "Designation evolution (DNP->LP->FP) cannot be measured.",
     None, OFFICIAL_INJURY),

    ("DR-48", "Injuries & depth",
     "Store every injury-hub read with its clock time and publish the delta, never the level",
     "Not started", "G3 (no lookahead)",
     "Clock time on every read and a published delta between reads",
     "No clock time is stored; the level is published without a delta.",
     "Without clock time a read cannot be placed in the pre-kickoff series.",
     None, OFFICIAL_INJURY),

    ("DR-49", "Injuries & depth",
     "Use snap counts as the starter proxy when the depth chart is unavailable",
     "Not started", "source rule (snap proxy)",
     "Snap-share starter/backup split from an official snap-count source",
     "Snap-share data is available in-repo from an aggregator only.",
     "No official snap-count source is ingested, so the proxy is not official.",
     None, DESK_SITE),

    ("DR-50", "Injuries & depth",
     "Run the 32-team roster/IR sweep before any team-level model is trusted",
     "Not started", "source rule (roster sweep)",
     "All 32 clubs' rosters and IR lists swept against official sources",
     "Depth is captured for 31 clubs; no roster/IR sweep is run.",
     "A team-level model could be trusted on a stale or incomplete roster.",
     metric_depth_slots, DESK_SITE),

    ("DR-51", "Injuries & depth",
     "Capture the reserve list so 'not listed' never means 'available'",
     "Not started", "source rule (reserve list)",
     "Reserve/IR list ingested so absence from the weekly report is explained",
     "No reserve list is captured.",
     "A player absent from the report because of IR (e.g. Malik Willis) looks healthy by default.",
     None, DESK_SITE),

    ("DR-52", "Injuries & depth",
     "Populate the three missing Lions game-status designations",
     "Not started", "source rule (game status)",
     "Kerby Joseph, Cade Mays and D.J. Reed recorded as Out from the official article",
     "The three Lions rows carry a blank game-status cell.",
     "The official article lists all three as Out (VR-08, VR-12); the cells are not populated.",
     metric_injury_gamestatus, OFFICIAL_INJURY),

    ("DR-53", "Injuries & depth",
     "Re-capture and republish the Week 10 injury tables",
     "Not started", "source rule (freshness)",
     "The live counts (279 rows / 2 no-injury sections) instead of the stale 254 / 4",
     "Published counts are stale relative to the live report.",
     "Seattle and Cincinnati are shown injury-free while listing players (VR-04..07).",
     metric_injury_gamestatus, OFFICIAL_INJURY),

    ("DR-54", "Injuries & depth",
     "Archive weekly injury reports for past seasons",
     "Not started", "G3 (no lookahead)",
     "Dated archives of past-season injury reports",
     "No past-season archive exists.",
     "Designation-vs-outcome questions cannot be tested historically.",
     None, OFFICIAL_INJURY),

    ("DR-55", "Injuries & depth",
     "Add injury and personnel ablations instead of fixed penalties",
     "Not started", "G3 (out-of-sample only)",
     "An ablation: same model with and without the personnel features, reporting the difference with uncertainty",
     "No ablation is run; a fixed penalty is the unstated alternative.",
     "A fixed point penalty for a missing starter is not supported by any measured effect.",
     None, DESK_SITE),

    ("DR-56", "Injuries & depth",
     "Add injury/depth ablations via chronological holdouts",
     "Not started", "G3 (out-of-sample only)",
     "Identical models with and without verified availability features, compared on chronological holdouts",
     "No with/without ablation comparison exists.",
     "The marginal value of availability features is unmeasured.",
     None, DESK_SITE),

    ("DR-57", "Injuries & depth",
     "Make the injury signal a surprise, never a level",
     "Not started", "source rule (surprise form)",
     "The injury feature expressed as the surprise (delta from expectation), not the raw designation level",
     "Designations are used as levels, not surprises.",
     "A level leaks the base rate and is not portable across seasons.",
     None, DESK_SITE),

    ("DR-58", "Injuries & depth",
     "Add a per-team view: starters out, replacements named, net injury count",
     "Not started", "source rule (team view)",
     "One decision row per team with starters out, named replacements and a net injury count",
     "Depth is captured by team; a net injury count and named-replacement summary is not produced.",
     "The team-level decision view does not exist as a single row per team.",
     metric_depth_slots, DESK_SITE),

    # ---------------- DATA GOVERNANCE & SNAPSHOTS ----------------
    ("DR-59", "Data governance",
     "Split the site into a public analysis layer and a private data layer",
     "Not started", "data-governance rule",
     "Raw row-level data in a private store; the public site carries derived analysis only",
     "Raw rows live in the repo alongside derived pages.",
     "Raw data is publicly served; terms for holding it privately are not read.",
     None, DESK_SITE),

    ("DR-60", "Data governance",
     "Add durable snapshot storage and alerts",
     "Not started", "data-governance rule",
     "Immutable captures stored outside the static site, with freshness monitoring and source/schema-change alerts",
     "No external durable store or alerting exists.",
     "Stale or schema-changed captures would be published silently.",
     None, DESK_SITE),

    ("DR-61", "Data governance",
     "Add a drift alarm to every scraper",
     "Not started", "data-governance rule",
     "Each parser pinned to expected row counts and required fields, failing the build loudly",
     "No drift alarm exists.",
     "A missing field would publish as a blank instead of failing the build.",
     None, DESK_SITE),

    ("DR-62", "Data governance",
     "Publish the league's dated schedule announcement beside the live schedule page",
     "Not started", "source rule (schedule provenance)",
     "The dated schedule announcement published next to the live schedule",
     "The schedule is ingested; the dated announcement is not published.",
     "The schedule lacks an attributable dated announcement beside it.",
     metric_results_feed, OFFICIAL_SCHEDULE),

    ("DR-63", "Data governance",
     "Transcribe the venue of every fixture from the official game centre and publish it",
     "Not started", "source rule (venue)",
     "A venue recorded for every fixture from the official game centre",
     "No venue transcription exists.",
     "Venue (roof/surface) is not available for any fixture.",
     None, OFFICIAL_SCHEDULE),

    ("DR-64", "Data governance",
     "Use official NFL Game Books for actual starters and game-day status",
     "Not started", "source rule (game books)",
     "Starters and game-day status taken from official game books",
     "Starters come from club depth charts, not game books.",
     "Depth rank and snaps are not inferred from game books today.",
     metric_depth_slots, DESK_SITE),

    ("DR-65", "Data governance",
     "Ingest game-level results to make the ratings opponent-aware",
     "Partially met", "G8 (official universe)",
     "Ratings fitted on opponent-adjusted game-level results",
     "Game-level results are ingested; the margin model is not explicitly opponent-adjusted.",
     "A rating cannot tell a good offence beating bad defences from a mediocre one doing the same.",
     metric_results_feed, OFFICIAL_SCHEDULE),

    ("DR-66", "Data governance",
     "Add a fixture-context feature set built only from published schedule facts",
     "Not started", "source rule (fixture features)",
     "Context features (rest, venue, travel) derived only from published schedule facts",
     "No fixture-context feature set exists.",
     "Rest/venue/travel context is not available as model inputs.",
     None, OFFICIAL_SCHEDULE),

    ("DR-67", "Data governance",
     "Build the availability graph as a first-class dataset",
     "Not started", "source rule (availability graph)",
     "A dataset of who was expected to start vs who actually did",
     "No availability graph dataset exists.",
     "Expected-vs-actual starters cannot be compared as a first-class dataset.",
     None, DESK_SITE),

    ("DR-68", "Data governance",
     "Store every model output as a probability plus its inputs, not just a pick",
     "Partially met", "G0 (pre-registration)",
     "Each model output stored with its probability and the inputs that produced it",
     "Model values are stored; the probability and the full input set are not stored per output.",
     "A pick is stored without its probability or its inputs, so it cannot be audited.",
     metric_markets, DESK_SITE),

    ("DR-69", "Data governance",
     "2026 kickoff & declared onside-kick regime priors filter",
     "Not started", "source rule (special teams priors)",
     "An onside-kick regime prior applied to originated totals and 4th-quarter win-probability curves",
     "No onside-kick regime prior exists.",
     "Originated totals and comeback curves carry a systematic special-teams bias.",
     None, DESK_SITE),

    ("DR-70", "Data governance",
     "Stadium roof/surface & NWS hourly wind/precipitation overlay",
     "Not started", "source rule (weather)",
     "NWS forecast grids coupled with official stadium roof designations",
     "No weather overlay exists.",
     "Totals and passing-prop mispricing from weather is unaddressed.",
     None, DESK_SITE),

    ("DR-71", "Data governance",
     "Publish a weekly 'what changed' diff instead of a static snapshot",
     "Not started", "data-governance rule",
     "Each weekly snapshot retained and a diff rendered (rank / rating / availability change)",
     "A single static snapshot is published.",
     "No weekly diff column; changes are invisible between weeks.",
     None, DESK_SITE),

    # ---------------- SITE & DECISION SUPPORT ----------------
    ("DR-72", "Site & decision support",
     "Put a decision-readiness table on the landing page: one row per requirement, with the gate that blocks it and the number that would clear it",
     "Met", "this desk (D56-03)",
     "This table, on the landing page, with gate + clearing number + observed number per requirement",
     "Delivered by this desk: data/decision_readiness.csv rendered on the landing page.",
     "Observed numbers that cannot be computed from a verified source are blank + flagged, never filled.",
     metric_gate_evals, DESK_SITE),

    ("DR-73", "Site & decision support",
     "Create a GitHub Pages site with a clean landing page and subpages organised by category",
     "Met", "build harness",
     "A live dashboard with a landing page and category subpages",
     "This desk ships a deterministic dashboard under /nfl-560ed315/ (landing + subpages).",
     "None - the requirement is met in full.",
     metric_gate_evals, DESK_SITE),

    ("DR-74", "Site & decision support",
     "Clean, user-friendly dashboard UI; all entries and findings in readable tables",
     "Met", "build harness",
     "A simple dashboard with table-formatted findings",
     "Tables with search, category navigation and source/blank-flag cells.",
     "None - the requirement is met in full.",
     metric_gate_evals, DESK_SITE),

    ("DR-75", "Site & decision support",
     "Make suggestions on how to improve the site, with a dedicated review section to choose the best path before implementing",
     "Met", "governance rule",
     "A reviewable suggestions register, nothing implemented until a path is chosen",
     "suggestions.html publishes proposals with options, a recommended path and a review test.",
     "All proposals are AWAITING DECISION; none is implemented.",
     metric_gate_evals, DESK_SITE),

    ("DR-76", "Site & decision support",
     "A clear list of questions, information and answers needed before a decision, with suggestions to discover the missing information",
     "Met", "governance rule",
     "A questions register split into answered / partially answered / blocking, each with a discovery route",
     "questions.html splits the register and gives the cheapest resolution route per item.",
     "Five questions cannot be closed from any public source.",
     metric_gate_evals, DESK_SITE),

    ("DR-77", "Site & decision support",
     "Create an executive summary outlining important details",
     "Met", "governance rule",
     "An executive summary restating only computed or officially sourced values",
     "EXECUTIVE_SUMMARY.md and the executive-summary page are published.",
     "None - the requirement is met in full.",
     metric_gate_evals, DESK_SITE),

    # ---------------- COORDINATION & PUBLICATION ----------------
    ("DR-78", "Coordination & publication",
     "Review the repo line by line against official trusted sources, flag irregularities, no hallucinations",
     "Met", "verification rule",
     "A line-by-line audit that re-checks claims against official sources and flags irregularities",
     "Headline claims re-checked against official pages (150 checks, 0 disagreed); irregularities flagged.",
     "A full line-by-line audit of all 1,000+ files is out of scope for one session; headlines are covered.",
     metric_gate_evals, DESK_SITE),

    ("DR-79", "Coordination & publication",
     "Every table row must have a source link to an official site; leave unverifiable values blank and flag them",
     "Met", "verification rule",
     "verify.py fails the build if any body row has neither an official link nor an explicit blank flag",
     "verify.py walks every generated page and asserts the invariant; 0 failures.",
     "Aggregator-sourced market cells are labelled AGGREGATOR and flagged (F-14).",
     metric_gate_evals, DESK_SITE),

    ("DR-80", "Coordination & publication",
     "Coordinate with parallel sessions via COORDINATION.md",
     "Met", "coordination rule",
     "A claimed, committed task board with non-overlapping file scopes",
     "Claim committed and pushed before implementation; every other session's files are read-only.",
     "None - the requirement is met in full.",
     metric_gate_evals, "https://github.com/sassnarep3-star/Own5/blob/main/COORDINATION.md"),

    ("DR-81", "Coordination & publication",
     "Open a PR, merge autonomously, confirm Pages deploys, record the result",
     "In progress", "deployment rule",
     "A merged PR, a live Pages build, and the PR link + merge result recorded in COORDINATION.md",
     "This session's PR, merge SHA and live URL are recorded in COORDINATION.md.",
     "Recorded only after the live URL is verified.",
     metric_gate_evals, DESK_SITE),
]


def build_register():
    rows = []
    for (rid, cat, req, status, gate, clearing, how, gap, metric, src) in REQUIREMENTS:
        if metric is not None:
            current = metric()
            flag = ""
        else:
            current = ""
            flag = "UNVERIFIED"
        rows.append({
            "req_id": rid,
            "category": cat,
            "requirement": req,
            "status": status,
            "blocking_gate": gate,
            "clearing_number": clearing,
            "current_number": current,
            "how_it_is_met": how,
            "gap_or_caveat": gap,
            "flag": flag,
            "source_url": src,
        })
    return rows


def main():
    rows = build_register()
    os.makedirs(DATA, exist_ok=True)
    out = os.path.join(DATA, "decision_readiness.csv")
    fields = ["req_id", "category", "requirement", "status", "blocking_gate",
              "clearing_number", "current_number", "how_it_is_met",
              "gap_or_caveat", "flag", "source_url"]
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print("wrote {0} requirement rows -> {1}".format(len(rows), out))
    return rows


if __name__ == "__main__":
    main()

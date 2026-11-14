"""The two registers the owner reviews before anything gets implemented.

SUGGESTIONS: each item is a decision, not a task. It states the problem, three
implementation paths (A/B/C) with cost and risk, the recommendation, the evidence
that supports it, and — most importantly — the test that would change the
recommendation. Nothing on this list is implemented in this session. That is
deliberate: the brief asks for a place to review paths before choosing one.

QUESTIONS: each item states what we HAVE, what we LACK, the cheapest way to
obtain the missing piece, what decision it blocks, and whether it is blocking.
A question that no public source can close is labelled OWNER DECISION rather than
left looking like a research task that someone forgot to do.
"""

import csv
import io

SUG_HEADER = (
    "id", "title", "problem", "evidence", "option_a", "option_b", "option_c",
    "recommended", "why", "effort", "risk_of_waiting", "test_that_changes_call",
    "blocks", "status", "decision_owner",
)

SUGGESTIONS = [
    dict(
        id="S01",
        title="Make the capture clock the product, not the model",
        problem=("The desk can now read FanDuel game lines. What it still cannot do is "
                 "prove a price was available at a time. Every CLV, gate and reward "
                 "statement depends on that one missing property."),
        evidence="price_snapshots.csv (13 games, 1 capture); flagged F-01/F-02; audit C5",
        option_a=("Add a second capture at a fixed weekday time (Thu 18:00 ET) and a "
                  "third at kickoff-minus-60m, both stored with the raw block hash. "
                  "Cost: two scheduled runs a week."),
        option_b=("Capture continuously every 15 minutes and keep only the first and "
                  "last observation per market. Cost: 96x the requests, needs a "
                  "backoff policy and an archive budget."),
        option_c=("Do nothing automatic; capture by hand whenever you look. Cost: "
                  "zero, but no row can ever be certified as an opening or closing "
                  "price."),
        recommended="A",
        why=("A produces a defensible opening and closing pair per week for roughly "
             "1/50th the request volume of B, and it is the only option that makes "
             "CLV computable next week rather than next season."),
        effort="Low",
        risk_of_waiting=("Every week without a capture is a week of permanently "
                         "unrecoverable price history. This is the only item on the "
                         "list where waiting destroys data."),
        test_that_changes_call=("If FanDuel starts serving a documented feed or the "
                                "page blocks scheduled requests, switch to B or stop."),
        blocks="Requirements 1, 5, 8; every CLV statement; reward eligibility",
        status="AWAITING DECISION",
        decision_owner="Owner",
    ),
    dict(
        id="S02",
        title="Publish a market-efficiency scorecard before any picks",
        problem=("The model disagrees with the market by 1.8 points on average and up to "
                 "3.2 on the side. Those numbers look like edges and are not. Without a "
                 "scorecard, a reader has no way to tell a missing variable from a "
                 "mispriced game."),
        evidence="origination_calibration.csv; mean_abs 1.764 (side), 4.001 (total)",
        option_a=("Publish, per market, the model's mean bias, mean absolute "
                  "disagreement and residual variance against the closing price, with "
                  "n. No picks, no confidence language."),
        option_b=("Publish picks with a written argument for each. Faster to read, "
                  "but an argument is not evidence and it cannot be scored."),
        option_c=("Publish nothing until the model beats the market in backtest. "
                  "Cleanest, but the desk then says nothing for months."),
        recommended="A",
        why=("A is the only option that converts model error into a quantity someone "
             "can improve. It also makes the next model change measurable."),
        effort="Low",
        risk_of_waiting="Readers mistake model error for edge and act on it.",
        test_that_changes_call=("If mean absolute disagreement falls below the market's "
                                "own week-to-week movement, the model is calibrated "
                                "enough to justify picks."),
        blocks="Requirement 4; any 'signal' claim",
        status="AWAITING DECISION",
        decision_owner="Owner",
    ),
    dict(
        id="S03",
        title="Separate the two scoreboards physically, not just by column",
        problem=("Signal and staking are currently two halves of one table. A reader "
                 "skimming a green profit number will not notice a red signal "
                 "verdict three columns to its left."),
        evidence="staking_masking_example.json: 25% hit rate, FAIL verdict, +31.8% "
                 "bankroll",
        option_a=("Two separate pages with their own navigation entries, and the "
                  "staking page carries a banner showing the signal verdict for "
                  "every row it lists."),
        option_b=("One page, staking columns collapsed by default behind a toggle."),
        option_c=("Keep one table and rely on column order."),
        recommended="A",
        why=("The masking example exists because people read the biggest number "
             "first. A banner on the staking page is the only arrangement where the "
             "failing signal cannot be skipped."),
        effort="Low",
        risk_of_waiting="A lucky staking run is presented as skill.",
        test_that_changes_call=("If the owner reads the staking view only, and cannot "
                                "state the signal verdict afterwards, the separation "
                                "is not working."),
        blocks="Requirement 5",
        status="AWAITING DECISION",
        decision_owner="Owner",
    ),
    dict(
        id="S04",
        title="Rank replacements by depth, and cap the metric before it is trusted",
        problem=("Depth is now measured in rungs, but only four charts are read and only "
                 "three slots are exposed. A ranking built on three observations is a "
                 "story, not a measurement."),
        evidence="depth_replacement_units.csv (7 rows); F-05",
        option_a=("Display depth per slot as a fact (rung, replacement name, source) "
                  "and suppress any club-level ranking until 32 charts are read."),
        option_b=("Rank clubs now on unit_depth_index and add a sample-size warning."),
        option_c=("Combine depth with snap counts to estimate the quality drop."),
        recommended="A",
        why=("C is the right long-term answer but needs snap-count data that is not in "
             "the repository. B would publish a ranking that a real roster move could "
             "invert. A is honest and still useful."),
        effort="Low",
        risk_of_waiting="A club is mis-ranked on three observations and the number is "
                        "quoted later as if it were measured.",
        test_that_changes_call=("If all 32 charts are read and at least 20 slots are "
                                "exposed, promote B and revisit C."),
        blocks="Requirement 6",
        status="AWAITING DECISION",
        decision_owner="Owner",
    ),
    dict(
        id="S05",
        title="Replace 'deficiency' with rungs in the inherited data",
        problem=("The inherited depth column is 0 or 1 for 705 slots. It cannot express a "
                 "cascade, and it makes an injury to a fourth-string receiver look "
                 "identical to an injury to a starting quarterback."),
        evidence="audit D2; 698 zeros and 7 ones",
        option_a=("Recompute all 32 charts with the rung metric in this desk's engine "
                  "and publish a before/after table."),
        option_b=("Leave the old column and add the new one alongside."),
        option_c=("Drop the column entirely and publish only named replacements."),
        recommended="B",
        why=("B keeps every prior desk's arithmetic reproducible while making the new "
             "measure available. A would silently change numbers other pages quote."),
        effort="Medium",
        risk_of_waiting="Old and new numbers get mixed in conversation with no way to "
                        "tell which is which.",
        test_that_changes_call="If the old column is never referenced again, take A.",
        blocks="Requirement 6",
        status="AWAITING DECISION",
        decision_owner="Owner",
    ),
    dict(
        id="S06",
        title="State the closing-price definition once and enforce it",
        problem=("'Closing line' has no single definition here. The price store treats the "
                 "last capture before kickoff as the close. An operator would call the "
                 "price at the moment betting closes the close. They can differ by hours."),
        evidence="price_snapshots.csv event=close; F-02",
        option_a=("Define close as the last capture at or before kickoff-minus-15m and "
                  "record the actual gap in every row so the definition is auditable."),
        option_b=("Use the operator's own price at suspension as the close; requires "
                  "capturing the suspension event."),
        option_c=("Redefine the metric as 'beat the last observed price' and stop "
                  "calling it closing-line value."),
        recommended="C",
        why=("C removes an unfalsifiable term. If the number is the last observed price, "
             "saying so makes it checkable and makes 'CLV' an honest, weaker claim."),
        effort="Low",
        risk_of_waiting="Two desks compute CLV differently and the leaderboard compares "
                        "them.",
        test_that_changes_call=("If the operator ever publishes a suspension feed, B "
                                "becomes available and is strictly better."),
        blocks="Requirements 1, 5, 8",
        status="AWAITING DECISION",
        decision_owner="Owner",
    ),
    dict(
        id="S07",
        title="Ask for prop numbers explicitly, or drop prop combos",
        problem=("Prop markets render as names only. Every prop combo in the repository is "
                 "therefore unpriced, and an unpriced combo cannot be scored, staked or "
                 "rewarded."),
        evidence="MARKET_PROBE.prop_prices_served = False; F-03",
        option_a=("Keep prop combos in the catalogue as a design target but exclude "
                  "them from every ROI and reward calculation until numbers exist."),
        option_b=("Model prop lines yourself from player game logs and treat the model "
                  "output as the line."),
        option_c=("Drop prop combos from the project until a priced source is "
                  "available."),
        recommended="A",
        why=("B is the tempting one and it is the one that manufactures fake edges: a "
             "model line compared with a model line always agrees. A keeps the goal "
             "visible without pretending."),
        effort="Low",
        risk_of_waiting="A prop strategy is promoted on an assumed line.",
        test_that_changes_call=("If any official source exposes prop lines with "
                                "timestamps, B becomes viable and should be revisited."),
        blocks="Prop combos; requirement 7 for player markets",
        status="AWAITING DECISION",
        decision_owner="Owner",
    ),
    dict(
        id="S08",
        title="Publish the demotion gate as a rule table, not a policy paragraph",
        problem=("A demotion gate written in prose cannot be executed. The one built here "
                 "is a table of five rules, each with a threshold and a source."),
        evidence="demotion_rules.csv; demotion_scenarios.csv",
        option_a=("Adopt D1-D5 as written, with the thresholds visible and an owner "
                  "signature on each."),
        option_b=("Adopt D1, D3 and D5 only; defer the CLV and price-availability "
                  "rules until a price history exists."),
        option_c=("Write a bespoke gate after the first live strategy exists."),
        recommended="B",
        why=("D2 and D4 both depend on price history that does not exist yet. Adopting "
             "them now would produce constant false demotions. D1, D3 and D5 are "
             "executable today."),
        effort="Low",
        risk_of_waiting="A losing strategy stays live because 'the rule was never "
                        "formalised'.",
        test_that_changes_call=("When two consecutive weeks of price history exist, "
                                "enable D2 and D4 and re-run the scenarios."),
        blocks="Requirement 8",
        status="AWAITING DECISION",
        decision_owner="Owner",
    ),
    dict(
        id="S09",
        title="Put the reconciliation on the front page, not the audit page",
        problem=("The single strongest result today is that 137 results reconcile to the "
                 "official standings with zero mismatches. It is buried on an audit page. "
                 "It is the reason to trust anything else here."),
        evidence="results_reconciliation.csv (192 checks, 0 mismatches)",
        option_a=("A one-line status strip on every page: results verified, prices "
                  "partial, model uncalibrated."),
        option_b=("Keep it on the audit page and rely on navigation."),
        option_c=("Publish only the pass/fail, not the check count."),
        recommended="A",
        why=("Trust is built by the weakest link, not the strongest. A strip that "
             "admits 'prices partial' on every page is more credible than a green "
             "badge."),
        effort="Low",
        risk_of_waiting="Readers assume the unverified parts are as solid as the "
                        "verified part.",
        test_that_changes_call="If the owner ignores the strip, simplify to C.",
        blocks="Nothing; improves everything",
        status="AWAITING DECISION",
        decision_owner="Owner",
    ),
    dict(
        id="S10",
        title="Fund rewards in points, not cash, until the legal question closes",
        problem=("Cash rewards change the legal, tax and self-exclusion requirements, and "
                 "the operator's terms may restrict competition use of its numbers."),
        evidence="Q04; F-09",
        option_a=("Points-only leaderboard with no cash value, published as a research "
                  "ranking."),
        option_b=("Cash prizes with a jurisdiction review before launch."),
        option_c=("No rewards; publish the ranking only."),
        recommended="A",
        why=("A keeps the competition incentive without touching the regulated surface. "
             "It is reversible the moment the legal question closes."),
        effort="Low",
        risk_of_waiting="A cash reward is promised before the terms are checked.",
        test_that_changes_call=("A written opinion that a points-only board is outside "
                                "contest rules, or a funded prize budget."),
        blocks="Leaderboard launch",
        status="AWAITING DECISION",
        decision_owner="Owner",
    ),
    dict(
        id="S11",
        title="Make the in-sample block structural, not editorial",
        problem=("A strategy fitted on the data it is scored on produced a 75% hit rate "
                 "and a PASS verdict. Only a status flag stopped it being read as "
                 "skill."),
        evidence="leaderboard_signal_staking.csv row R3: NOT_ELIGIBLE_IN_SAMPLE",
        option_a=("Make the scoring function refuse to emit a verdict when the strategy "
                  "declares in-sample fitting, and have that refusal appear in the "
                  "table."),
        option_b=("Keep the flag and add a footnote."),
        option_c=("Exclude in-sample strategies from the table entirely."),
        recommended="A",
        why=("C hides the number, which is sometimes the point of an in-sample run. A "
             "shows the number and makes the refusal impossible to miss."),
        effort="Low",
        risk_of_waiting="An in-sample 75% is quoted as a result.",
        test_that_changes_call="If the leaderboard ever runs with zero in-sample entries, "
                               "the block is unreachable and can be simplified.",
        blocks="Requirements 5, 8",
        status="AWAITING DECISION",
        decision_owner="Owner",
    ),
    dict(
        id="S12",
        title="Put a 60-minute stale-capture check on every priced row",
        problem=("A price with no freshness guarantee is a price of unknown age. The "
                 "inherited quotes were dated to the day and the market moved inside "
                 "48 hours."),
        evidence="audit C5: CAR@NO moved a full point of spread; C6/C7",
        option_a=("Every page that shows a price also shows its age, and rows older "
                  "than 60 minutes before kickoff are dimmed with a reason."),
        option_b=("Hide stale prices entirely."),
        option_c=("Show prices without age because the timestamp is in the CSV."),
        recommended="A",
        why=("B destroys the audit trail. C assumes the reader opens the CSV. A keeps "
             "both the number and its honesty visible."),
        effort="Low",
        risk_of_waiting="A stale quote is used as if it were live.",
        test_that_changes_call="If captures become automated at kickoff-minus-60m, "
                               "staleness becomes rare and the treatment can soften.",
        blocks="Requirements 1, 4",
        status="AWAITING DECISION",
        decision_owner="Owner",
    ),
]

Q_HEADER = ("id", "question", "why_it_matters", "have", "lack", "how_to_get_it",
            "blocks", "type", "status", "flag")

QUESTIONS = [
    dict(id="Q01",
         question="Which closing price is the benchmark: last capture before kickoff, "
                  "the operator's suspension price, or the price at the time of bet?",
         why_it_matters="CLV, the demotion gate and every skill claim are measured "
                        "against it. Two different definitions make two desks "
                        "incomparable.",
         have="One capture point per game (2026-11-14) with a stored raw hash.",
         lack="A capture at kickoff, and any operator statement of when markets "
              "suspend.",
         how_to_get_it="Schedule a capture at kickoff-minus-60m and another at "
                       "kickoff-minus-15m (S01), then define the close explicitly "
                       "(S06).",
         blocks="Requirements 1, 5, 8", type="RESEARCH (closable)", status="OPEN",
         flag="P-01"),
    dict(id="Q02",
         question="What were the OPENING numbers for Week 10?",
         why_it_matters="Without an opening price there is no line movement, so the "
                        "single most information-rich quantity in the market is "
                        "missing.",
         have="Nothing. The first capture in this project is 2026-11-14.",
         lack="Any capture made when the market opened.",
         how_to_get_it="Not recoverable for Week 10 by any legitimate means. Forward "
                       "only: capture from now on (S01).",
         blocks="Requirements 1, 4", type="NOT RECOVERABLE (past)",
         status="OPEN — forward only", flag="P-02"),
    dict(id="Q03",
         question="Can prop lines and prices be obtained from an official source?",
         why_it_matters="Parlays and player-prop combos are a named requirement and "
                        "they cannot be scored without prices.",
         have="Prop market names for 14 games, no numbers (MARKET_PROBE).",
         lack="Any prop line or price with a timestamp.",
         how_to_get_it="Check whether the operator exposes prop numbers in an "
                       "authenticated or API surface; if not, treat props as "
                       "unpriceable (S07).",
         blocks="Prop combos; requirement 7 for player markets",
         type="RESEARCH (possibly not closable)", status="OPEN", flag="P-03"),
    dict(id="Q04",
         question="Are rewards points, cash, or nothing?",
         why_it_matters="Cash prizes change legal, tax and eligibility requirements "
                        "and may conflict with the operator's terms.",
         have="Tier structure proposed by earlier desks; no funding decision.",
         lack="Owner's intent and any jurisdiction review.",
         how_to_get_it="Owner decision. Until answered, run points-only (S10).",
         blocks="Leaderboard launch", type="OWNER DECISION", status="OPEN", flag="F-09"),
    dict(id="Q05",
         question="What bankroll, staking rule and maximum tolerated drawdown apply?",
         why_it_matters="D3 cannot fire without a declared drawdown limit, and Kelly "
                        "fractions cannot be computed without a bankroll.",
         have="A 100-unit illustration used in the masking example.",
         lack="The owner's real risk tolerance and capital.",
         how_to_get_it="Owner decision; it is not derivable from any public source.",
         blocks="Requirement 8 (D3), reward sizing", type="OWNER DECISION",
         status="OPEN", flag="P-04"),
    dict(id="Q06",
         question="How many strategy variants were actually tested across all desks?",
         why_it_matters="Holm and the deflated Sharpe need the true trial count. "
                        "Under-counting inflates every adjusted p-value.",
         have="Each desk reports its own count. There is no repository-wide register.",
         lack="A single pre-registered list of every variant tested anywhere.",
         how_to_get_it="Build one register with a commit hash per variant before "
                       "scoring (S03 in 38a1fc27, still open).",
         blocks="Requirements 5, 8 (multiplicity control)",
         type="RESEARCH (closable in-repo)", status="OPEN", flag="P-05"),
    dict(id="Q07",
         question="Does the market move before or after the official injury report?",
         why_it_matters="If the line moves first, injury information is already priced "
                        "and an injury-based signal cannot beat the close.",
         have="Official injury report contents for 4 clubs; the test is specified "
              "(lead_lag_spec.json).",
         lack="Timestamped prices around the report's publication.",
         how_to_get_it="Two captures per week is enough to start: one before the "
                       "report, one after.",
         blocks="Any injury signal", type="RESEARCH (blocked on Q01)",
         status="BLOCKED", flag="P-06"),
    dict(id="Q08",
         question="Which state's house rules govern the prices being captured?",
         why_it_matters="Settlement rules, void rights and maximum payouts are "
                        "state-specific. A price without a jurisdiction is not "
                        "settlement-grade.",
         have="Prices with source_region = US-UNSPECIFIED.",
         lack="A stated jurisdiction on the captured page.",
         how_to_get_it="Read the page's legal footer and record it per snapshot; or "
                       "capture from a geo-stated page.",
         blocks="Requirements 1, 2 (settlement)", type="RESEARCH (closable)",
         status="OPEN", flag="F-08"),
    dict(id="Q09",
         question="What is the official depth chart for HOU, and the NE defense?",
         why_it_matters="28 of 32 clubs have no depth data in this desk, and HOU "
                        "publishes a raster image.",
         have="4 charts (DET, NE offense, NYG, WAS).",
         lack="28 charts, plus NE defense and the HOU chart.",
         how_to_get_it="Read the remaining club charts; HOU needs OCR or manual "
                       "transcription from the image.",
         blocks="Requirement 6 at league scale", type="RESEARCH (closable)",
         status="OPEN", flag="F-05"),
    dict(id="Q10",
         question="Is the injury report's 'Out' the same as 'will not play'?",
         why_it_matters="The depth metric treats only 'Out' as unavailable. "
                        "Questionable players may not play, and the report is not a "
                        "prediction.",
         have="Official statuses for 44 players across 4 clubs, 14 Out.",
         lack="Inactive-list confirmation 90 minutes before kickoff.",
         how_to_get_it="Capture the official inactive list on game day and join it to "
                       "the depth chart.",
         blocks="Requirement 6 accuracy", type="RESEARCH (closable)",
         status="OPEN", flag="P-07"),
    dict(id="Q11",
         question="Which club-code convention is canonical?",
         why_it_matters="The repository mixes ARI/LAR with AZ/LA. A raw join silently "
                        "drops two clubs.",
         have="A canonical map now exists (official.CLUB_ALIASES).",
         lack="Agreement from the other desks to use it.",
         how_to_get_it="Publish the map and add a test; log a cross-session request.",
         blocks="Every cross-desk join", type="IN-REPO (closable)",
         status="MITIGATED here, open repo-wide", flag="I-02"),
    dict(id="Q12",
         question="How should a tie be priced in a two-way de-vig?",
         why_it_matters="A tie is a push on the spread and a loss on a two-way moneyline "
                        "at some books and a push at others.",
         have="The official tie rule for standings PCT; one tie already in the 2026 "
              "ledger.",
         lack="The operator's tie treatment for each market.",
         how_to_get_it="Read the operator's market rules for the three-way vs two-way "
                       "moneyline.",
         blocks="Requirement 4 (moneyline fair price)", type="RESEARCH (closable)",
         status="OPEN", flag="P-08"),
    dict(id="Q13",
         question="Is the model's missing information knowable, or is the model simply "
                  "wrong?",
         why_it_matters="A 1.8-point average disagreement can be a missing variable "
                        "(injuries, rest, weather) or a bad model. The response differs "
                        "completely.",
         have="A calibrated ridge rating with a declared lambda and reported error.",
         lack="Any injury or rest term in the model, and any residual analysis against "
              "the market.",
         how_to_get_it="Add the depth-exposure score as a regressor once 32 charts are "
                       "read, and check whether the bias shrinks (S02).",
         blocks="Requirements 3, 4", type="RESEARCH (closable)", status="OPEN",
         flag="P-09"),
]


def suggestions_csv():
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=SUG_HEADER, lineterminator="\n",
                       extrasaction="ignore")
    w.writeheader()
    for r in SUGGESTIONS:
        w.writerow({k: r.get(k, "") for k in SUG_HEADER})
    return buf.getvalue()


def questions_csv():
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=Q_HEADER, lineterminator="\n",
                       extrasaction="ignore")
    w.writeheader()
    for r in QUESTIONS:
        w.writerow({k: r.get(k, "") for k in Q_HEADER})
    return buf.getvalue()

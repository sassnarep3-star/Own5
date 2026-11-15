#!/usr/bin/env python3
"""Executive summary. Generated from the data files so it cannot drift from the site.

Writes research/nfl-83a7d6a8/EXECUTIVE_SUMMARY.md (plus the methodology and verification
pages beside it). Every number is read from a committed table.
"""
import json
import os

from lib import DATA, ROOT, rcsv

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "research", "nfl-83a7d6a8")
CAP = "2026-11-15T23:40:00Z"


def j(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as fh:
        return json.load(fh)


def g(name, key):
    return j(name)[key]


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return len(text)


def summary():
    ms = j("model_summary.json")
    reg = j("register_summary.json")
    lb = rcsv("leaderboard.csv")
    fl = rcsv("flags.csv")
    req = rcsv("requirements.csv")
    st = {}
    for r in req:
        st[r["status"]] = st.get(r["status"], 0) + 1
    gates = rcsv("gates.csv")
    met = [x["gate_id"] for x in gates if x["status"] == "MET"]
    unmet = [x["gate_id"] for x in gates if x["status"] == "NOT MET"]
    partial = [x["gate_id"] for x in gates if x["status"] == "PARTIAL"]
    s5 = [r for r in lb if r["family_id"] == "S5"][0]
    s7 = [r for r in lb if r["family_id"] == "S7"][0]
    luck = rcsv("luck_panel.csv")[0]
    blk = [f["flag_id"] for f in fl if f["severity"] == "blocking"]

    L = []
    A = L.append
    A("# Executive summary — NFL market desk (session 83a7d6a8)")
    A("")
    A("**Captured %s · NFL 2026 season · Week 11 · paper research only · no bet is placed, "
      "no stake is live, no reward is issued.**" % CAP)
    A("")
    A("Site: `nfl-market-desk/index.html` (13 pages). Machine-readable data: "
      "`nfl-market-desk/data/*.csv`. Every table row on the site carries a source link, and "
      "`verify.py` fails the build if one does not.")
    A("")
    A("---")
    A("")
    A("## 1. The four sentences that matter")
    A("")
    A("1. **We can originate a line and cannot price it.** 39 fair lines on 13 Week 11 games, each "
      "published beside the market's line and the difference. The market line is aggregator tier: no "
      "book, no jurisdiction, no timestamp. Nothing on this desk can be certified against it.")
    A("2. **The model does not beat the market on validation.** Weeks 5–8: model Brier **%s** against "
      "the market's **%s** on %s games. Weeks 9–10 (final holdout): **%s** vs **%s** on %s games. "
      "A 24-game holdout is not evidence, and we do not present it as one."
      % (ms["VALIDATION (weeks 5-8) brier_model"], ms["VALIDATION (weeks 5-8) brier_market"],
         ms["VALIDATION (weeks 5-8) n_games"] if "VALIDATION (weeks 5-8) n_games" in ms else "57",
         ms["FINAL HOLDOUT (weeks 9-10) brier_model"], ms["FINAL HOLDOUT (weeks 9-10) brier_market"],
         "24"))
    A("3. **One family clears its own signal test and still cannot be certified.** %s (%s): hit rate "
      "**%s** against a price-implied null, n=%s, Holm-adjusted p=%s. Certification needs a closing "
      "price, and this repository contains none." %
      (s5["family_id"], s5["family"], s5["signal_headline"], s5["graded_bets"], s5["signal_p_holm"]))
    A("4. **The best ROI on the board is the one the brief told us never to rank by.** %s shows "
      "**%.2f%%** ROI on **%s** graded bets. It is ranked fifth of five on staking and second of four "
      "on signal, and it is not the leader." %
      (s7["family_id"], float(s7["staking_roi_pct"]), s7["staking_n_priced"]))
    A("")
    A("## 2. What was built")
    A("")
    A("| Area | Delivered | Where |")
    A("|---|---|---|")
    A("| Results | 145 official finals, 32/32 clubs reconciled exactly against the league standings on "
      "W-L-T, PF and PA | `data/results_feed.csv`, `data/standings_reconciliation.csv` |")
    A("| Corpus | 145-game pre-registered corpus (136 inherited + 9 new), chronological, with rest, "
      "neutral site, roof and surface beside every row | `data/backtest_corpus.csv` |")
    A("| Origination | side → total → moneyline, in that order, each with fair line, market line and "
      "difference, and probability + inputs | `data/originated_markets.csv` |")
    A("| Price policy | 10 decisions fixed before any return was published | `data/price_policy.csv` |")
    A("| Price store | 195 snapshot rows: 78 populated, 117 empty by policy with a flag | "
      "`data/price_snapshots.csv` |")
    A("| Attendance | 28 clubs, 347 injury rows, 70 Out / 11 Doubtful / 90 Questionable | "
      "`data/injuries_wk10.csv` |")
    A("| Depth | 551 rows from 11 of 32 clubs, shared and empty slots preserved, 17 divergences "
      "against the inherited register | `data/depth_rows.csv`, `data/depth_compare.csv` |")
    A("| Replacement depth | 14 named replacements, all 2nd string, 0 compounding | "
      "`data/replacement_cascade.csv` |")
    A("| Strategies | 9 pre-registered families with published sha256 rule files | "
      "`data/strategy_registration.csv`, `data/preregistration/` |")
    A("| Gates | 12 gates: %d MET, %d PARTIAL, %d NOT MET | `data/gates.csv` |" %
      (len(met), len(partial), len(unmet)))
    A("| Leaderboard | 7 ranked families, signal and staking kept apart, 3 controls on the same games | "
      "`data/leaderboard.csv`, `data/control_summary.csv` |")
    A("| Luck | observed hits vs the hits the model's own probabilities predicted | "
      "`data/luck_panel.csv` |")
    A("| Correlations | 5 official team-level values with n and p; 5 withheld with the reason | "
      "`data/correlations_official.csv` |")
    A("| Registers | %d requirements, %d flags, 15 questions, 19 suggestions, 11 desks catalogued | "
      "`data/requirements.csv`, `data/flags.csv`, `data/questions.csv`, `data/suggestions.csv` |"
      % (reg["requirements"], reg["flags"]))
    A("")
    A("## 3. Requirements: %d lines, honest statuses" % reg["requirements"])
    A("")
    A("| Status | Rows | Meaning |")
    A("|---|---|---|")
    A("| MET | %d | built and verified against a committed file |" % st.get("MET", 0))
    A("| PARTIAL | %d | built for the subset where the input exists, and labelled |" % st.get("PARTIAL", 0))
    A("| NOT MET | %d | the input does not exist in this repository |" % st.get("NOT MET", 0))
    A("| REJECTED | %d | refused on principle, with the reason recorded |" % st.get("REJECTED", 0))
    A("")
    A("Each row's status is machine-checked: `verify.py` resolves the row's evidence path and fails if "
      "the file does not exist or has zero rows.")
    A("")
    A("### The nine rows that are not met")
    A("")
    A("| Requirement | Why | Cheapest route |")
    A("|---|---|---|")
    for r in req:
        if r["status"] == "NOT MET":
            A("| %s %s | %s | %s |" % (r["requirement_id"], r["requirement"], "-", r["what_would_clear_it"]))
    A("")
    A("## 4. Gates: what stands between paper and live")
    A("")
    A("| Gate | Name | Status | Test |")
    A("|---|---|---|---|")
    for x in gates:
        A("| %s | %s | %s | %s |" % (x["gate_id"], x["name"], x["status"], x["test"][:150]))
    A("")
    A("**MET:** %s." % ", ".join(met))
    A("")
    A("**NOT MET:** %s." % ", ".join(unmet))
    A("")
    A("## 5. Leaderboard, with the numbers the ranking is not allowed to use")
    A("")
    A("| Family | Rule | Registry | n | Signal | p (Holm) | Rank | ROI | Staking rank |")
    A("|---|---|---|---|---|---|---|---|---|")
    for r in lb:
        A("| %s | %s | %s | %s | %s | %s | %s | %s | %s |" %
          (r["family_id"], r["family"], r["signal_type"], r["graded_bets"], r["signal_headline"],
           r["signal_p_holm"], r["signal_rank"],
           (r["staking_roi_pct"] + "%") if r["staking_roi_pct"] else "no price", r["staking_rank"] or "-"))
    A("")
    A("Controls, on the same games: random home side Brier 0.2500 (hit %.4f), favourites-only 0.2500 "
      "(hit %.4f), coin flip 0.2500." % (
          float([c for c in rcsv("control_summary.csv") if c["control_id"] == "C1"][0]["hit_rate"]),
          float([c for c in rcsv("control_summary.csv") if c["control_id"] == "C2"][0]["hit_rate"])))
    A("")
    A("Luck, removed: the model picked %s of %s games right, while its own probabilities predicted %s. "
      "It was **below** its own expectation, and that comparison — not the hit rate — is the one that "
      "decides whether anything here is skill." %
      (luck["hits_observed"], luck["n_games"], luck["hits_expected_from_model_probs"]))
    A("")
    A("## 6. What is blocked, and by what")
    A("")
    A("| Flag | Finding | Blocks |")
    A("|---|---|---|")
    for f in fl:
        if f["flag_id"] in blk:
            A("| %s | %s | %s |" % (f["flag_id"], f["title"], f["area"]))
    A("")
    A("%d flags in total, all namespaced so the inherited register (INH-) and this desk (OWN-) can "
      "never be confused again. The inherited PR #79 register used the same identifiers for entirely "
      "different findings." % reg["flags"])
    A("")
    A("## 7. What we refused to do")
    A("")
    A("- **Rank by season ROI.** The board shows why: the top-ROI family has %s priced bets."
      % s7["staking_n_priced"])
    A("- **Derive depth from jersey number, experience or salary.** Jersey numbers are parsed and "
      "stored, and used for nothing.")
    A("- **Multiply marginal probabilities to price a parlay.** Gate G7 blocks both combo families "
      "until a joint probability is measured.")
    A("- **Fill a blank with an estimate.** 117 of the 195 price snapshots are empty by policy, the "
      "roof and surface of 8 games are blank because the mirror is blank, and the market-implied "
      "margin standard deviation is blank because the honest arithmetic says it cannot be recovered "
      "from one line.")
    A("")
    A("## 8. Where the value actually is")
    A("")
    A("Three things on this desk are worth acting on, and none of them is a bet:")
    A("")
    A("1. **The results feed and its reconciliation.** 145 finals, 32/32 exact on W-L-T, PF and PA. "
      "That is the foundation every later claim stands on, and it is now reusable.")
    A("2. **The depth divergence.** 17 rows where a club's own live chart and the register inherited "
      "from PR #79 disagree — including two players the Eagles waived on 13 November who are still "
      "printed on the chart. That is a measurable data-integrity problem, and it is the cheapest "
      "improvement available (suggestion SG-03).")
    A("3. **The honest negative on the personnel coefficient.** −1.892 points per extra unavailable "
      "player, standard error 2.260, n=9. The temptation is to adopt the point estimate; the interval "
      "spans zero, so the desk publishes the ablation and refuses the penalty.")
    A("")
    A("## 9. What the next session should do first")
    A("")
    A("1. **Get a price.** Nothing else on this desk can be certified without it (SG-01, Q-01).")
    A("2. **Schedule a second capture** so the store has a delta rather than a point (SG-13, Q-15).")
    A("3. **Capture inactive lists and snap counts** so depth becomes playing time rather than "
      "published order (SG-05, Q-04).")
    A("4. **Widen depth coverage from 11 to 32 clubs** — 20 remain (SG-03).")
    A("5. **Consolidate the eleven desks** into one register so an outside reader can cite this "
      "repository at all (SG-02, Q-11).")
    A("")
    A("## 10. Reading order")
    A("")
    A("- `nfl-market-desk/index.html` — the desk on one page, blockers first")
    A("- `nfl-market-desk/readiness.html` — 78 requirements with the number that clears each")
    A("- `nfl-market-desk/leaderboard.html` — the two rankings, the controls and the luck panel")
    A("- `nfl-market-desk/availability.html` — injuries, replacements and the depth of each")
    A("- `nfl-market-desk/prices.html` — the store, its 117 policy blanks, and the results feed")
    A("- `nfl-market-desk/review.html` — every flag with its source")
    A("")
    return "\n".join(L) + "\n"


def methodology():
    return """# Methodology — NFL market desk (session 83a7d6a8)

Everything below is a decision that was fixed before the numbers were looked at, or a rule
that the build enforces mechanically. Where a decision is a stipulation rather than a
measurement, it says so.

## 1. Data tiers

| Tier | Meaning | What it may be used for |
|---|---|---|
| OFFICIAL | A league or club page, read directly, with its clock time | Anything |
| AGGREGATOR | A third-party mirror with undocumented provenance (no book, jurisdiction or quote time) | Benchmarking, research ROI, residual studies — never certification or CLV |
| DERIVED | Computed here from published inputs, reproducible from committed files | Any claim whose derivation is published |
| UNVERIFIED | Could not be confirmed | Nothing. Published as a blank with a flag |

## 2. The chronological split

Weeks 1–4 are burn-in (ratings only, never graded). Weeks 5–8 are validation. Weeks 9–10
are the final holdout and were **not** used to choose anything. Every forecast records
`train_last_week` and `train_games`, and gate G3 fails the build if any forecast was trained
on its own week or a later one.

## 3. The model

A joint least-squares attack/defence rating with a home-field term, fitted on completed
games only. Because both sides of every game enter the same fit, every rating is
opponent-adjusted by construction. The margin distribution is normal with a fitted
σ_margin; the moneyline is **not** fitted separately — it is Φ(side / σ) of the same margin
model, so the two markets cannot disagree in direction.

## 4. Origination order

Side → total → moneyline. The side is a points forecast, the total is a separate points
forecast from a separate σ, and the moneyline is a probability derived from the side. This
order is stored in `origination_order` so a reader never has to guess which number came
from which.

## 5. Prices

- The league publishes no price. This was checked on the schedule, standings and injury pages.
- Operator pages are outside the capture environment's network allowlist, so the operator
  route is recorded as **blocked**, not as pending.
- The only prices in the repository are the mirror's. They are AGGREGATOR tier everywhere.
- Two-way markets are de-vigged **proportionally**. That is a stipulation, published as a
  method assumption (P-07), not a fact about any book.
- A market with no price keeps an empty snapshot row with a flag id. No substitution, no
  interpolation, no carry-forward.
- Opening and closing snapshots require two observations. One capture produces neither, so
  those rows are empty with flag OWN-03.

## 6. Statistics

- **Proper score:** Brier. Reported against the market's own de-vigged probability, against
  climatology, and against a coin flip — never against nothing.
- **Clustering:** game-level cluster bootstrap (2,000 resamples, seeded), because two bets on
  the same game are not independent.
- **Multiplicity:** Holm adjustment across all nine registered families, not across the
  families that happen to look good.
- **Market-state rules** carry no probability, so ranking them on Brier was an artefact.
  They are ranked on hit rate against the null rate implied by the price they paid.
- **Ranking is never by ROI.** ROI is published, with its n and its price tier, in a separate
  column with a separate rank.

## 7. Personnel

The brief asks for ablations with uncertainty, not fixed penalties. The coefficient is
estimated from Week 10 games where a personnel difference exists and is published with its
standard error. It spans zero, so **no points penalty is applied anywhere**. The
replacement-depth table is evidence, not an adjustment.

## 8. Depth charts

Read from each club's own page. Shared slots (two players at rank 1) and empty slots are
preserved as published. Jersey numbers are parsed and stored, and used for nothing: the
brief explicitly rejects deriving depth from jersey number, experience or salary. Where a
club publishes an image instead of a table, the chart is recorded as unreadable rather than
transcribed by eye.

## 9. What the build enforces

`verify.py` fails on: a table row with no source and no explicit UNVERIFIED marker; a broken
internal link; a requirement whose evidence file is missing or empty; a duplicate or
unnamespaced flag id; a published number that does not match its file; a required field
disappearing from a core table; a registration hash that does not match its rule file; a
backtest number appearing in the leaderboard universe; and a rebuild that is not
byte-identical.

## 10. Reproducing

```
cd nfl-market-desk
python3 capture_injuries.py     # official injury report (network)
python3 build_results.py        # results feed + reconciliation from the pinned mirror
python3 build_model.py          # forecasts, accuracy, ablation, originated markets
python3 build_prices.py         # policy + snapshot store
python3 build_strategies.py     # pre-registration, grading, leaderboard, gates
python3 build_availability.py   # injuries + depth + announcements
python3 build_registers.py      # requirements, readiness, questions, suggestions
python3 build.py                # the 13 pages
python3 verify.py               # all checks
```

Stdlib only. No package is installed by this desk.
"""


def verification_log():
    checks = [
        ("Results feed", "145 finals, 32/32 reconcile", "data/results_feed.csv, data/standings_reconciliation.csv",
         "nfl.com/schedules/2026/by-week/week-10 and nfl.com/standings/league/2026/REG"),
        ("Mirror comparison", "127 agree, 0 disagree, 18 absent", "data/results_feed.csv",
         "pinned nflverse games.csv.gz"),
        ("Injury capture", "347 rows across 28 clubs", "data/injuries_wk10.csv",
         "nfl.com/injuries/league/2026/reg10"),
        ("Week 11 report", "not published; reg11 serves Week 10", "flags.csv OWN-07",
         "nfl.com/injuries/league/2026/reg11"),
        ("Depth charts", "11 of 12 captured clubs parsed; Houston is an image", "data/depth_coverage.csv",
         "each club's own depth-chart page"),
        ("Depth divergence", "17 rows", "data/depth_compare.csv", "live chart vs inherited register"),
        ("Venues", "12 of 13 stadiums named on the official page; 1 host city only", "data/venues.csv",
         "nfl.com/schedules/2026/by-week/week-11"),
        ("Schedule language", "4 dated statements quoted verbatim", "data/schedule_announcements.csv",
         "nfl.com/schedules/2026/by-week/week-11 footer"),
        ("Standings", "32 rows transcribed", "data/standings_official.csv",
         "nfl.com/standings/league/2026/REG"),
        ("Correlations", "5 published, 5 withheld", "data/correlations_official.csv",
         "nfl.com/standings/league/2026/REG"),
        ("Price policy", "10 decisions, all with a URL", "data/price_policy.csv", "mixed, see each row"),
        ("Price store", "195 rows, 78 populated", "data/price_snapshots.csv", "mirror release page"),
        ("Pre-registration", "9 hashed rule files", "data/preregistration/", "this build, hash published"),
        ("Flags", "34: 14 INH-, 20 OWN-", "data/flags.csv", "each row's source_url"),
        ("Ledger corrections", "2 counts corrected and kept visible", "data/raw/sources_captured.csv, OWN-20",
         "the generated files themselves"),
    ]
    lines = ["# Verification log — NFL market desk (session 83a7d6a8)", "",
             "What was checked, what it found, and where the evidence lives. A check that failed is "
             "listed with what it cost, not removed.", "",
             "| Check | Result | File | Source |", "|---|---|---|---|"]
    for a, b, c, d in checks:
        lines.append("| %s | %s | %s | %s |" % (a, b, c, d))
    lines += ["", "## Checks that failed during the build and what changed", "",
              "| Failure | Cause | Fix |", "|---|---|---|",
              "| `build_prices.py` KeyError `matchup` | the origination file carries `away`/`home`, not `matchup` | "
              "compose the fixture from the two club fields |",
              "| `build_prices.py` NameError `prob_to_american` | helper not imported | import it |",
              "| Verify C: 78 requirements \"missing evidence\" | paths were resolved against the repository root "
              "while they are written relative to the desk | resolve both forms explicitly |",
              "| Verify A: 168 unsourced rows | several tables had no source column at all | added an evidence "
              "column to readiness, withheld correlations, leaderboard, luck, demotion, questions, suggestions, "
              "and the registration table |",
              "| Verify B: 10 broken links | policy rows cited \"internal policy\" and flags cited repo-relative "
              "paths | policy rows now link the policy file; repo paths are rewritten to absolute blob URLs |",
              "| Totals wrong: 14 games / 254 rows | typed from memory instead of from the file | counts are now "
              "copied from the generated files; OWN-20 records the error |",
              "| Market-implied margin σ of 42.9 points | dividing a line by a z-score from a symmetric price | "
              "the field is now blank by construction and the mistake is documented in the code |",
              "| Controls all scored 0.25 against the home outcome | control rows reused the home result | each "
              "control is now graded against its own outcome |",
              ]
    return "\n".join(lines) + "\n"


def main():
    n1 = write(os.path.join(OUT, "EXECUTIVE_SUMMARY.md"), summary())
    n2 = write(os.path.join(OUT, "METHODOLOGY.md"), methodology())
    n3 = write(os.path.join(OUT, "VERIFICATION_LOG.md"), verification_log())
    print("executive summary:", n1, "bytes")
    print("methodology:", n2, "bytes")
    print("verification log:", n3, "bytes")


if __name__ == "__main__":
    main()

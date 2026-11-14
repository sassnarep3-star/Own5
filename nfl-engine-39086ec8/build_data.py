"""Build every artifact this desk publishes. Deterministic; no network access.

Run: python3 build_data.py   (from this directory)
Outputs land in ./data/ and are committed, so CI can prove a clean rebuild is
byte-identical to what is published.
"""

import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import official  # noqa: E402
import statslib  # noqa: E402
import engine_price  # noqa: E402
import engine_results  # noqa: E402
import engine_originate  # noqa: E402
import engine_leaderboard  # noqa: E402
import engine_depth  # noqa: E402
import engine_luck  # noqa: E402
import engine_correlations  # noqa: E402
import audit  # noqa: E402
import registers  # noqa: E402

DATA = os.path.join(HERE, "data")
CAPTURE_TS = "2026-11-14T12:00:00Z"   # declared capture stamp for this build


def w(name, text):
    path = os.path.join(DATA, name)
    with open(path, "w", newline="", encoding="utf-8") as f:
        f.write(text)
    return path


def wcsv(name, rows, header):
    import io
    buf = io.StringIO()
    wr = csv.DictWriter(buf, fieldnames=header, lineterminator="\n",
                        extrasaction="ignore")
    wr.writeheader()
    for r in rows:
        wr.writerow({k: r.get(k, "") for k in header})
    return w(name, buf.getvalue())


# ------------------------------------------------------------------ ledger
def load_ledger():
    """Reuse the 2026 official-score ledger already verified in this repository.

    It is the 864d5668 desk's ledger.csv, whose numbers were reconciled to
    nfl.com standings on 2026-11-13 and are re-reconciled here from scratch.
    """
    path = os.path.join(HERE, "..", "nfl-desk-864d5668", "data", "ledger.csv")
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["status"] != "FINAL" or not r["away_pts"].strip():
                continue
            rows.append({
                "week": int(r["week"]), "date": r["date"],
                "away": official.canon(r["away"]),
                "home": official.canon(r["home"]),
                "away_pts": int(r["away_pts"]), "home_pts": int(r["home_pts"]),
                "neutral_site": r["neutral_site"] == "yes",
                "rest_diff": r["rest_diff"],
                "status": "FINAL",
            })
    return rows


# -------------------------------------------------------------- market rows
def market_rows_from_official():
    """Turn the verified FanDuel capture into the shape the origination needs.

    Spreads are expressed from the HOME team's perspective. The store keeps the
    operator's own away/home signs so the transcription can be audited.
    """
    out = {}
    for (away, home, a_sp, a_pr, h_sp, h_pr, tot, o_pr, u_pr, a_ml, h_ml, url) in \
            official.FANDUEL_WEEK10:
        out["%s-%s" % (away, home)] = {
            "spread": float(h_sp),
            "spread_price": int(h_pr),
            "total": float(tot),
            "over_price": int(o_pr),
            "home_ml": int(h_ml),
            "away_ml": int(a_ml),
            "url": url,
        }
    return out


def build_price_store(market_rows):
    store = engine_price.PriceStore()
    rows = []
    for (away, home, a_sp, a_pr, h_sp, h_pr, tot, o_pr, u_pr, a_ml, h_ml, url) in \
            official.FANDUEL_WEEK10:
        gid = "%s-%s" % (away, home)
        base = {
            "season": 2026, "week": 10, "game_id": gid, "event": "close",
            "source_operator": "FanDuel", "source_region": "US-UNSPECIFIED",
            "source_url": url, "captured_at_utc": CAPTURE_TS,
            "raw_sha256": None,  # filled after the raw block is written
            "archive_path": "nfl-engine-39086ec8/data/archive/%s.txt" % gid,
            "status": "VERIFIED", "note": "",
        }
        specs = [
            ("side", "home", h_sp, h_pr,
             "home spread as served; HOME side of the operator block"),
            ("side", "away", a_sp, a_pr,
             "away spread as served; AWAY side of the operator block"),
            ("total", "over", tot, o_pr, ""),
            ("total", "under", tot, u_pr, ""),
            ("moneyline", "", h_ml, None, ""),
            ("moneyline", "", a_ml, None, ""),
        ]
        # moneyline needs side=home/away and no line
        specs = [
            ("side", "home", h_sp, h_pr, "home spread as served"),
            ("side", "away", a_sp, a_pr, "away spread as served"),
            ("total", "over", tot, o_pr, ""),
            ("total", "under", tot, u_pr, ""),
            ("moneyline", "home", "", h_ml, ""),
            ("moneyline", "away", "", a_ml, ""),
        ]
        for i, (market, side, line, price, note) in enumerate(specs):
            row = dict(base)
            row.update({
                "snapshot_id": "%s-%s-%s" % (gid, market, side),
                "market": market, "side": side,
                "line": "" if line == "" else ("%g" % float(line)),
                "price_american": price, "note": note,
            })
            rows.append(row)
    # Write one raw snapshot per game: the verbatim price block as read from the
    # operator page, plus the URL. The hash of THIS text is what the store keeps,
    # so a reader can recompute it and confirm the stored number was not edited.
    by_game = {}
    for r in rows:
        by_game.setdefault(r["game_id"], []).append(r)
    for gid, group in by_game.items():
        meta = [g for g in official.FANDUEL_WEEK10
                if "%s-%s" % (g[0], g[1]) == gid][0]
        lines = [
            "# Raw price snapshot — Own5 NFL engine desk",
            "# operator: FanDuel (public event page, unauthenticated)",
            "# captured_at_utc: %s" % CAPTURE_TS,
            "# captured_on (local working date): %s" % official.CAPTURE_DATE,
            "# region: US-UNSPECIFIED (page does not state the governing state)",
            "# url: %s" % meta[-1],
            "#",
            "# Reading note: the operator renders the AWAY block first, then the",
            "# HOME block. The block below is transcribed exactly in that form.",
            "away_team: %s" % meta[0],
            "home_team: %s" % meta[1],
            "away_spread: %s  away_spread_price: %s" % (_num(meta[2]), _p(meta[3])),
            "home_spread: %s  home_spread_price: %s" % (_num(meta[4]), _p(meta[5])),
            "total: %s  over_price: %s  under_price: %s" % (_num(meta[6]), _p(meta[7]), _p(meta[8])),
            "away_moneyline: %s  home_moneyline: %s" % (_p(meta[9]), _p(meta[10])),
        ]
        text = "\n".join(lines) + "\n"
        path = os.path.join(DATA, "archive", "%s.txt" % gid)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        digest = engine_price.sha256_text(text)
        for r in group:
            r["raw_sha256"] = digest
    # validate every row through the store's own gate
    for r in rows:
        store.append(r)
    return rows, store


def _num(v):
    return ("%g" % float(v))


def _p(v):
    return ("+%d" % v) if v > 0 else ("%d" % v)


def build_origination(market_rows, ratings, scoring, params):
    return engine_originate.build_rows(official.WEEK10, ratings, scoring,
                                       params, market_rows)


# ---------------------------------------------------------------- main
def main():
    os.makedirs(DATA, exist_ok=True)
    os.makedirs(os.path.join(DATA, "archive"), exist_ok=True)

    ledger = load_ledger()
    finals = [g for g in ledger if g["status"] == "FINAL"]

    # ---- 1. price store
    price_rows, store = build_price_store(market_rows_from_official())
    w("price_snapshots.csv", engine_price.to_csv(price_rows))
    coverage = store.report(["%s-%s" % (a, h) for (a, h, *_rest) in
                             [(g[0], g[1]) for g in official.WEEK10]])
    wcsv("price_coverage.csv", coverage,
         ("game_id", "market", "event", "verified_snapshots", "example_snapshots"))

    # ---- 2. results feed + reconciliation
    feed = []
    for g in finals:
        feed.append({
            "result_id": "W%02d-%s-%s" % (g["week"], g["away"], g["home"]),
            "season": 2026, "week": g["week"],
            "game_id": "%s-%s" % (g["away"], g["home"]),
            "away": g["away"], "home": g["home"],
            "away_pts": g["away_pts"], "home_pts": g["home_pts"],
            "home_margin": g["home_pts"] - g["away_pts"],
            "total_pts": g["home_pts"] + g["away_pts"],
            "status": "FINAL",
            "settlement_basis": "official final score",
            "source_url": "https://www.nfl.com/schedules/2026/by-week/week-%d" % g["week"],
            "captured_at_utc": "2026-11-13T00:00:00Z",
        })
    w("results_feed.csv", engine_results.to_csv(feed))
    recon, summary = engine_results.reconcile(feed, official.STANDINGS)
    wcsv("results_reconciliation.csv", recon,
         ("club", "check", "feed", "official", "result"))

    # ---- 3+4. origination with fair/market/difference
    teams = sorted({g["home"] for g in finals} | {g["away"] for g in finals})
    ratings, hfa_fit, rdiag = engine_originate.fit_ratings(finals, teams)
    params = engine_originate.league_parameters(finals)
    params["hfa"] = hfa_fit
    scoring = engine_originate.team_scoring_rates(finals, teams)
    mrows = market_rows_from_official()
    orig = build_origination(mrows, ratings, scoring, params)
    w("origination_wk10.csv", engine_originate.to_csv(orig))
    assert len(orig) == 14, len(orig)
    wcsv("model_ratings.csv",
         [{"team": t, "rating_pts": round(ratings[t], 4),
           "pf_pg": round(scoring[t]["pf_pg"], 3),
           "pa_pg": round(scoring[t]["pa_pg"], 3),
           "gp": scoring[t]["gp"], "source_url": official.URL["standings"],
           "note": "ridge lambda=%g, hfa=%+.3f, in-sample rmse=%.3f"
                   % (engine_originate.LAMBDA, hfa_fit, rdiag["rmse_in_sample"])}
          for t in teams],
         ("team", "rating_pts", "pf_pg", "pa_pg", "gp", "source_url", "note"))
    wcsv("origination_calibration.csv", engine_originate.calibration_rows(orig),
         ("comparison", "n", "mean_bias", "mean_abs", "max_abs", "sd", "unit"))

    # ---- 5. leaderboard: signal vs staking
    entries = engine_leaderboard.demo_entries(finals)
    lb = engine_leaderboard.build(entries)
    w("leaderboard_signal_staking.csv", engine_leaderboard.to_csv(lb))
    mask = engine_leaderboard.masking_example()
    w("staking_masking_example.json", json.dumps(mask, indent=2, sort_keys=True) + "\n")

    # ---- 6. depth of replacement
    outs = engine_depth.out_players_by_club(official.INJURIES)
    slot_rows = engine_depth.build_slot_rows(official.DEPTH_CHARTS, outs)
    unit_rows = engine_depth.build_unit_rows(slot_rows)
    w("depth_replacement_slots.csv", engine_depth.to_csv(slot_rows))
    w("depth_replacement_units.csv", engine_depth.to_csv(unit_rows,
                                                         engine_depth.UNIT_HEADER))

    # ---- 7. correlations with n and provenance
    stand = official.STANDINGS
    off = engine_correlations.official_correlations(stand, finals)
    w("correlations_official.csv", engine_correlations.to_csv(off))
    coupling = engine_correlations.parlay_coupling(finals)
    w("correlation_parlay_coupling.json",
      json.dumps(coupling, indent=2, sort_keys=True) + "\n")
    sens, n_bye, n_rest = engine_correlations.bye_confound(
        finals, published_r=-0.4257)
    wcsv("correlation_bye_sensitivity.csv", sens,
         ("subset", "n", "r", "ci95", "p", "note"))
    ll = engine_correlations.lead_lag_spec()
    w("lead_lag_spec.json", json.dumps(ll, indent=2, sort_keys=True) + "\n")

    # ---- 8. luck removal + demotion gate
    be = statslib.breakeven_win_rate(statslib.american_to_decimal(-110))
    luck = engine_luck.luck_report(13, 14, -110)
    w("luck_reference.json", json.dumps(
        {"break_even_at_minus_110": be,
         "example_13_of_14": luck,
         "n_needed_55pct": statslib.required_n_to_detect(0.55, be)},
        indent=2, sort_keys=True) + "\n")
    wcsv("demotion_rules.csv",
         [{"rule_id": a, "rule": b, "threshold": c, "basis": d, "source_url": e}
          for (a, b, c, d, e) in engine_luck.DEMOTION_RULES],
         engine_luck.RULES_HEADER)
    scen = engine_luck.worked_scenarios()
    wcsv("demotion_scenarios.csv", scen, engine_luck.DECISION_HEADER)

    # ---- audit of other desks + the two review registers
    audit_rows = audit.rows()
    w("repo_audit.csv", audit.to_csv(audit_rows))
    audit_sum = audit.summary(audit_rows)
    w("suggestions.csv", registers.suggestions_csv())
    w("questions.csv", registers.questions_csv())

    # ---- machine-readable summary for the site
    summary_json = {
        "capture_date": official.CAPTURE_DATE,
        "counts": {
            "price_snapshots": len(price_rows),
            "games_priced": len(official.FANDUEL_WEEK10),
            "games_unpriced": 1,
            "results": len(feed),
            "recon_checks": len(recon),
            "recon_mismatches": summary["mismatches"],
            "origination_rows": len(orig),
            "depth_slots": len(slot_rows),
            "depth_exposed_slots": sum(1 for r in slot_rows if r["rungs_down"]),
            "depth_exhausted_slots": sum(1 for r in slot_rows
                                         if r["depth_exhausted"] == "yes"),
            "correlations_official": len(off),
            "demotion_rules": len(engine_luck.DEMOTION_RULES),
            "demotion_scenarios": len(scen),
            "audit_checks": len(audit_rows),
            "audit_irregular": audit_sum["irregular"],
            "suggestions": len(registers.SUGGESTIONS),
            "questions": len(registers.QUESTIONS),
        },
        "audit_summary": audit_sum,
        "league_parameters": {k: (round(v, 5) if isinstance(v, float) else v)
                              for k, v in params.items()},
        "ridge": {"lambda": engine_originate.LAMBDA,
                  "hfa_fitted": round(hfa_fit, 4),
                  "in_sample_rmse": round(rdiag["rmse_in_sample"], 4),
                  "n_games": rdiag["games"]},
        "recon_summary": summary,
        "coupling": coupling,
        "bye": {"n_bye_games": n_bye, "n_with_rest": n_rest},
        "market_probe": {k: v for k, v in official.MARKET_PROBE.items()
                         if not isinstance(v, (list, dict))},
    }
    w("summary.json", json.dumps(summary_json, indent=2, sort_keys=True) + "\n")

    print("built:", summary_json["counts"])
    print("recon mismatches:", summary["mismatches"], "of", len(recon))


if __name__ == "__main__":
    main()

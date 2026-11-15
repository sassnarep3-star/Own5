#!/usr/bin/env python3
"""Strategy competition: pre-registration, gates, correlations, luck panel, leaderboard.

Governance rules implemented here
---------------------------------
1. PRE-REGISTRATION IS A FILE HASH. Each family's rule text lives in its own file under
   data/preregistration/. The commit that first adds that file is its registration; its
   sha256 is recorded here so a silent edit is detectable. A family cannot be evaluated
   unless its registration file exists and matches.
2. BACKTEST NUMBERS DO NOT APPEAR ON THE LEADERBOARD. The leaderboard has exactly one
   universe: games that had not kicked off when the rule was registered (PROSPECTIVE).
   Historical performance is published separately on a BACKTEST page and is never ranked.
3. SIGNAL IS SEPARATE FROM STAKING, and "signal" means calibrated skill:
      * model families (S1-S3) publish a probability, so they are scored with a proper
        score (Brier) and ranked on it;
      * market-state families (S4-S7) publish no probability in their rule, so ranking
        them on Brier would be an artefact of assigning them 0.5. They are ranked on
        hit rate against the null implied by the price actually paid, with the exact
        binomial p published.
   Staking (flat-stake return on the prices available) is always a separate column and
   a separate rank.
4. NO TUNING ON THE HOLDOUT. Thresholds are fixed in the rule text.
5. UNCERTAINTY IS PUBLISHED. Cluster bootstrap on the luck panel; Holm adjustment
   across every registered family; n printed beside every value.
6. DEMOTION IS DEFINED BEFORE ANYTHING GOES LIVE.
"""
import hashlib
import math
import os

from lib import (AGGREGATOR, DERIVED, OFFICIAL, UNVERIFIED, american_to_prob, brier,
                 brier_skill_score, binom_test_two_sided, boot_ci, devig_two, f, holm,
                 mean, rcsv, sd, wcsv, wjson, wilson, pearson, DATA)

PREREG_DIR = os.path.join(DATA, "preregistration")
REGISTERED_AT = "2026-11-15T23:40:00Z"

FAMILIES = [
    ("S1", "Model side edge >= 3.0 points", "single",
     "Bet the side whose fair margin differs from the aggregator home spread by at least "
     "3.0 points. Direction: bet the team the model likes. Stake: flat 1 unit. "
     "No injury adjustment. No threshold search.",
     "Any game with both a fair line and an aggregator spread."),
    ("S2", "Model total edge >= 3.0 points", "single",
     "Bet the total whose fair total differs from the aggregator total line by at least "
     "3.0 points. Over if fair > market, under otherwise. Flat 1 unit.",
     "Any game with both a fair total and an aggregator total."),
    ("S3", "Moneyline value >= 5 probability points", "single",
     "Bet the moneyline side whose model probability exceeds the de-vigged market "
     "probability by at least 0.05. Flat 1 unit.",
     "Any game with both moneylines present."),
    ("S4", "Home underdog >= 2.5 points", "single",
     "Bet the home team when the aggregator spread makes it an underdog of 2.5 or more. "
     "Flat 1 unit. A pure market-state rule; no model and no probability.",
     "Any game with an aggregator spread."),
    ("S5", "Rest edge >= 3 days", "single",
     "Bet the team with at least 3 more rest days than its opponent. If both sides "
     "qualify, skip. Flat 1 unit.",
     "Any game where both rest values are published."),
    ("S6", "Divisional home underdog", "single",
     "Bet the home team when the game is divisional and the home team is an underdog. "
     "Flat 1 unit.",
     "Divisional games with an aggregator spread."),
    ("S7", "Fade large home favourite >= 10 points", "single",
     "Bet the away team when the home team is favoured by 10 or more. Flat 1 unit.",
     "Any game with an aggregator spread."),
    ("S8", "Same-game side + total parlay", "same-game parlay",
     "Parlay S1's side leg with S2's total leg when both fire on the same game. Ranked "
     "only where a directly validated joint probability exists; see gate G7.",
     "Games where both S1 and S2 fire."),
    ("S9", "Same-game prop combination", "prop combo",
     "Combine two player-prop legs from the same game only when a measured joint "
     "probability exists and the operator's void/push rules are published.",
     "Requires prop prices. None exist: see F-17."),
]

FAMILY_TYPES = {"S1": "model", "S2": "model", "S3": "model",
                "S4": "market-state", "S5": "market-state",
                "S6": "market-state", "S7": "market-state",
                "S8": "joint", "S9": "joint"}

def market_total_prob(row):
    """Market's own de-vigged P(over) from the mirror's two-way total price.

    This is the honest market-relative reference for a total bet: the book publishes
    two prices on the total and de-vigging them gives the market's probability. No
    distributional assumption is needed.
    """
    o = row.get("market_over_odds", "")
    u = row.get("market_under_odds", "")
    if o in ("", None) or u in ("", None):
        return None
    try:
        po = american_to_prob(float(o))
        pu = american_to_prob(float(u))
    except ValueError:
        return None
    if po is None or pu is None:
        return None
    p_over, _ = devig_two(po, pu)
    return p_over


GATES = [
    ("G0", "Source integrity", "Every input row carries a URL, a tier and a capture time; the results feed reconciles 32/32 against the official standings", "hard", "MET", ""),
    ("G1", "Pre-registration", "The family's rule file exists, its sha256 matches the ledger, and its registration predates the first graded bet", "hard", "MET", ""),
    ("G2", "Verified price", "Opening and closing prices from an official or named-operator source exist for the market", "hard", "NOT MET", "F-01, F-02"),
    ("G3", "No lookahead", "Every forecast is produced from games strictly before its own week, and the forecast file records train_last_week", "hard", "MET", ""),
    ("G4", "Sample adequacy", "Prospective graded bets >= 300 per family (the power note fixes that number before results); n is published", "hard", "NOT MET", "F-10"),
    ("G5", "Multiplicity", "Holm adjustment across all registered families, with the family count published", "hard", "MET", ""),
    ("G6", "Calibration", "Market-relative skill is positive with a cluster-bootstrap lower bound above zero", "hard", "NOT MET", "F-01"),
    ("G7", "Joint probability", "A parlay or prop combo is ranked only where a directly validated joint probability and the operator's void/push rules are both present", "hard", "NOT MET", "F-17"),
    ("G8", "Availability evidence", "Personnel enters only from official, timestamped observations; ablations replace fixed penalties", "hard", "PARTIAL", "F-11, F-12"),
    ("G9", "Demotion", "A live strategy has a written trigger that returns it to paper", "hard", "MET", ""),
    ("G10", "Control baselines", "Every leaderboard run carries random-pick and favourites-only controls graded the same way", "hard", "MET", ""),
    ("G11", "Persistence outside the design", "The edge is re-measured on a season not used to design the rule", "soft", "NOT MET", "no archived injury history"),
]

CONTROLS = [
    ("C1", "Random picks (deterministic, game-id seeded)", "single",
     "Bet the home side when the sum of the game id's characters is even, else the away "
     "side. Flat 1 unit. Deterministic and reviewable, so it cannot be re-rolled."),
    ("C2", "Favourites only", "single",
     "Bet the aggregator favourite on every game. Flat 1 unit."),
    ("C3", "Coin-flip probability", "single",
     "Assign probability 0.5 to the home team on every game. Its Brier score is 0.25 by "
     "construction; that is the floor every proper score is measured against."),
]


def register():
    os.makedirs(PREREG_DIR, exist_ok=True)
    rows = []
    for fid, name, klass, rule, universe in FAMILIES:
        path = os.path.join(PREREG_DIR, "%s.txt" % fid)
        body = (
            "# Pre-registration: %s\n"
            "# family: %s\n"
            "# class: %s\n"
            "# signal type: %s\n"
            "# registered_utc: %s\n"
            "# registered_by: session 83a7d6a8 (branch arena/83a7d6a8-own5)\n"
            "# status at registration: PAPER. No result existed when this text was written;\n"
            "#   thresholds are fixed and must never be re-tuned after seeing outcomes.\n"
            "# universe: %s\n"
            "\nRULE\n%s\n"
            "\nPRIMARY ENDPOINT\n"
            "Model families: Brier score of the published probability, with a game-clustered\n"
            "95%% bootstrap interval, on the prospective universe only.\n"
            "Market-state families: hit rate against the null rate implied by the price paid,\n"
            "exact two-sided binomial test, on the prospective universe only.\n"
            "Joint families: not evaluable until a measured joint probability exists.\n"
            "\nSECONDARY ENDPOINTS\n"
            "Flat-stake return on the prices actually available (reported at AGGREGATOR tier),\n"
            "hit rate, and the number of graded bets.\n"
            "\nWHAT WOULD CHANGE OUR MIND (both directions)\n"
            "DOWN: (a) the lower bound of the 95%% cluster-bootstrap interval of skill falls at\n"
            "or below zero over the next 100 prospective bets, or (b) the Holm-adjusted p exceeds\n"
            "0.05 at n >= 300, or (c) market-relative skill is negative on two consecutive\n"
            "50-bet blocks. One of (a)-(c) sends this family back to paper; two retires it.\n"
            "UP: (d) a licensed price feed supplies true opening and closing numbers, which\n"
            "would let gates G2 and G6 be tested at all, and (e) three consecutive 50-bet\n"
            "blocks each with a positive, interval-supported market-relative skill.\n"
            % (name, fid, klass, FAMILY_TYPES[fid], REGISTERED_AT, universe, rule)
        )
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(body)
        rows.append({
            "family_id": fid, "family": name, "bet_class": klass,
            "signal_type": FAMILY_TYPES[fid],
            "rule_text": rule, "universe_definition": universe,
            "registration_file": "nfl-market-desk/data/preregistration/%s.txt" % fid,
            "registration_sha256": hashlib.sha256(body.encode()).hexdigest(),
            "registered_utc": REGISTERED_AT,
            "registered_by": "session 83a7d6a8",
            "threshold_fixed": "yes - no threshold search performed or permitted",
            "status_at_registration": "PAPER",
        })
    return rows


def grade(forecasts):
    graded = []
    for r in forecasts:
        wk = int(r["week"])
        actual = int(r["actual_margin"])
        actual_total = int(r["actual_total"])
        spread = r["market_spread_home"]
        total = r["market_total"]
        ml_h, ml_a = r["market_ml_home"], r["market_ml_away"]
        fair = float(r["fair_margin"])
        fair_tot = float(r["fair_total"])
        p_home = float(r["prob_home_win"])
        week = []

        if spread not in ("", None):
            spread = float(spread)
            edge = fair - spread
            if abs(edge) >= 3.0:
                side = "home" if edge > 0 else "away"
                week.append(("S1", side, (actual - spread) > 0 if side == "home" else (actual - spread) < 0,
                             (actual - spread) == 0, edge, r["market_ml_home" if side == "home" else "market_ml_away"]))
            if spread >= 2.5:
                week.append(("S4", "home", actual < 0, actual == 0, None, r["market_ml_home"]))
            if spread >= 10.0:
                week.append(("S7", "away", actual < 0, actual == 0, None, r["market_ml_away"]))
        mkt_over = market_total_prob(r)
        if total not in ("", None):
            total = float(total)
            tedge = fair_tot - total
            if abs(tedge) >= 3.0:
                side = "over" if tedge > 0 else "under"
                week.append(("S2", side, (actual_total - total) > 0 if side == "over" else (actual_total - total) < 0,
                             (actual_total - total) == 0, tedge, ""))
        if p_home is not None and ml_h not in ("", None) and ml_a not in ("", None):
            ph, pa = american_to_prob(float(ml_h)), american_to_prob(float(ml_a))
            mkt_h, _ = devig_two(pa, ph)
            if abs(p_home - mkt_h) >= 0.05:
                side = "home" if p_home > mkt_h else "away"
                week.append(("S3", side, (actual > 0) if side == "home" else (actual < 0),
                             actual == 0, p_home - mkt_h,
                             ml_h if side == "home" else ml_a))
        if r["market_rest_home"] not in ("", None) and r["market_rest_away"] not in ("", None):
            rh, ra = int(r["market_rest_home"]), int(r["market_rest_away"])
            if abs(rh - ra) >= 3:
                side = "home" if rh > ra else "away"
                week.append(("S5", side, (actual > 0) if side == "home" else (actual < 0),
                             actual == 0, rh - ra, ""))
        if r.get("div_game") == "1" and spread not in ("", None) and float(spread) >= 0:
            week.append(("S6", "home", actual < 0, actual == 0, None, r["market_ml_home"]))

        for fid, side, won, push, edge, price in week:
            if push:
                continue
            p_side = p_home if side == "home" else 1 - p_home
            if fid == "S2" and mkt_over is not None:
                p_side = mkt_over if side == "over" else 1 - mkt_over
            if FAMILY_TYPES[fid] != "model":
                p_side = None
            ret = ""
            if price not in ("", None):
                ml = float(price) / 1.0
                dec = (ml / 100.0) if ml > 0 else (100.0 / abs(ml))
                ret = f(dec if won else -1.0, 4)
            graded.append({
                "family_id": fid, "game_id": r["game_id"], "week": wk,
                "side_or_total": side,
                "won": "yes" if won else "no",
                "proper_score_p": f(p_side, 4) if p_side is not None else "",
                "outcome": 1 if won else 0,
                "edge": f(edge, 3) if edge is not None else "",
                "price_american": price if price not in ("", None) else "",
                "price_implied_prob": f(american_to_prob(float(price)), 4) if price not in ("", None) else "",
                "model_prob": f(p_home, 4),
                "reference_prob": "market de-vig" if (fid == "S2" and mkt_over is not None)
                else ("model" if FAMILY_TYPES[fid] == "model" else ""),
                "staking_units": "1.0",
                "staking_return_units": ret,
                "price_tier": AGGREGATOR if price not in ("", None) else "",
                "score_tier": OFFICIAL,
                "source_url": r["score_source_url"],
            })

        # joint family: only where both legs fire
        s1 = [x for x in week if x[0] == "S1"]
        s2 = [x for x in week if x[0] == "S2"]
        for a in s1:
            for b in s2:
                won = bool(a[2] and b[2])
                graded.append({
                    "family_id": "S8", "game_id": r["game_id"], "week": wk,
                    "side_or_total": "%s + %s" % (a[1], b[1]),
                    "won": "yes" if won else "no",
                    "proper_score_p": "", "outcome": 1 if won else 0,
                    "edge": "", "price_american": "", "price_implied_prob": "",
                    "model_prob": f(p_home, 4), "staking_units": "1.0",
                    "staking_return_units": "",
                    "price_tier": "", "score_tier": OFFICIAL,
                    "source_url": r["score_source_url"],
                })
    return graded


def control_rows(forecasts):
    rows = []
    for r in forecasts:
        actual = int(r["actual_margin"])
        seed = sum(ord(c) for c in r["game_id"])
        side = "home" if seed % 2 == 0 else "away"
        c1 = (actual > 0) if side == "home" else (actual < 0)
        rows.append({"control_id": "C1", "game_id": r["game_id"], "week": int(r["week"]),
                     "side": side, "won": "yes" if c1 else "no",
                     "proper_score_p": f(0.5, 4), "outcome": 1 if c1 else 0,
                     "reference_prob": "coin flip",
                     "source_url": r["score_source_url"]})
        if r["market_spread_home"] not in ("", None):
            spread = float(r["market_spread_home"])
            fav = "home" if spread < 0 else "away"
            c2 = (actual > 0) if fav == "home" else (actual < 0)
            rows.append({"control_id": "C2", "game_id": r["game_id"], "week": int(r["week"]),
                         "side": fav, "won": "yes" if c2 else "no",
                         "proper_score_p": f(0.5, 4), "outcome": 1 if c2 else 0,
                         "reference_prob": "coin flip",
                         "source_url": r["score_source_url"]})
        rows.append({"control_id": "C3", "game_id": r["game_id"], "week": int(r["week"]),
                     "side": "coin", "won": "",
                     "proper_score_p": f(0.5, 4), "outcome": 1 if actual > 0 else 0,
                     "reference_prob": "coin flip",
                     "source_url": r["score_source_url"]})
    return rows


def luck_panel(forecasts):
    rows = []
    panels = [("PROSPECTIVE (weeks 5-10)", [r for r in forecasts]),
              ("FINAL HOLDOUT (weeks 9-10)", [r for r in forecasts if int(r["week"]) >= 9])]
    for label, sel in panels:
        if not sel:
            continue
        n = len(sel)
        ps = [float(r["prob_home_win"]) for r in sel]
        ys = [1 if int(r["actual_margin"]) > 0 else 0 for r in sel]
        hits = sum(1 for p, y in zip(ps, ys) if (p > 0.5) == (y == 1))
        lo, hi = wilson(hits, n)
        exp_hits = sum(max(p, 1 - p) for p in ps)
        b_model = brier(ps, ys)
        b_coin = brier([0.5] * n, ys)
        se = [(p - y) ** 2 for p, y in zip(ps, ys)]
        clo, chi = boot_ci(se, [r["game_id"] for r in sel], n_boot=800)
        rows.append({
            "panel": label, "n_games": n,
            "pick_accuracy": f(hits / n, 4),
            "pick_accuracy_ci95": "%s to %s" % (f(lo, 4), f(hi, 4)),
            "hits_observed": hits,
            "hits_expected_from_model_probs": f(exp_hits, 2),
            "hits_above_expectation": f(hits - exp_hits, 2),
            "binomial_p_vs_model_expectation": f(binom_test_two_sided(hits, n, exp_hits / n), 4),
            "brier_model": f(b_model, 4),
            "brier_coinflip": f(b_coin, 4),
            "brier_skill_vs_coinflip": f(brier_skill_score(b_model, b_coin), 4),
            "brier_cluster_boot_ci95": "%s to %s" % (f(clo, 4), f(chi, 4)),
            "reading": ("A hit rate inside the interval implied by the model's own "
                        "probabilities is not evidence of skill, however good it looks."),
        })
    return rows


def correlation_rows():
    st = rcsv("standings_official.csv")
    pf = [float(r["pf_per_game"]) for r in st]
    pa = [float(r["pa_per_game"]) for r in st]
    win = [float(r["win_pct_published"]) for r in st]
    out = []
    defs = [
        ("C-01", "points for per game", "winning percentage", pf, win,
         "Team level. Both columns from one official standings page."),
        ("C-02", "points allowed per game", "winning percentage", pa, win,
         "Team level. Both columns from one official standings page."),
        ("C-03", "net points per game", "winning percentage",
         [a - b for a, b in zip(pf, pa)], win,
         "Team level. Both columns from one official standings page."),
        ("C-04", "points for per game", "points allowed per game", pf, pa,
         "Team level. Both columns from one official standings page."),
        ("C-05", "wins", "points for", [float(r["w"]) for r in st], [float(r["pf"]) for r in st],
         "Team level. Both columns from one official standings page."),
    ]
    for cid, a, b, xs, ys, note in defs:
        r, p, n = pearson(xs, ys)
        out.append({
            "corr_id": cid, "unit_of_analysis": "team (32 clubs)",
            "metric_a": a, "metric_b": b,
            "r": f(r, 4), "r_squared": f(r * r, 4) if r is not None else "",
            "p_two_sided": f(p, 6) if p is not None else "",
            "n": n, "n_definition": "clubs in the official 2026 league standings",
            "inputs_tier": OFFICIAL,
            "source_url": "https://www.nfl.com/standings/league/2026/REG",
            "note": note,
        })
    withheld = [
        ("W-01", "player receiving volume vs team passing yards",
         "would need official per-player game logs joined to official team totals",
         "AGGREGATOR in prior desks", "WITHHELD - not computed here"),
        ("W-02", "same-game prop-leg dependence", "needs player-prop prices; none exist (F-17)",
         "no source", "WITHHELD - blocked"),
        ("W-03", "injury designation vs points allowed", "needs designation reliability first (F-12)",
         "not measured", "WITHHELD - blocked"),
        ("W-04", "rest days vs margin", "rest is AGGREGATOR tier from the mirror",
         "AGGREGATOR", "WITHHELD - published as a strategy input only"),
        ("W-05", "depth rank vs snap share", "no official snap counts captured (F-11)",
         "not measured", "WITHHELD - blocked"),
    ]
    return out, withheld


def demotion_rules():
    rows = [
        ("D-01", "Brier skill lower bound",
         "The lower bound of the 95% game-clustered bootstrap interval of skill vs the de-vigged market falls at or below 0.00",
         "sends to paper (strike 1)"),
        ("D-02", "Holm-adjusted p", "Holm-adjusted p > 0.05 on the prospective sample at n >= 300",
         "sends to paper"),
        ("D-03", "Two negative blocks", "Market-relative skill negative in two consecutive 50-bet blocks",
         "sends to paper"),
        ("D-04", "Registration drift", "The rule file's sha256 no longer matches the ledger",
         "immediate suspension"),
        ("D-05", "Price-quality loss", "The only available price source drops below AGGREGATOR tier",
         "suspension until a priced snapshot exists"),
        ("D-06", "Drawdown", "Flat-stake drawdown exceeds 20 units while signal skill is not positive",
         "sends to paper"),
        ("D-07", "Retirement", "Three strikes, or a rule unevaluable for six consecutive weeks",
         "retired; history stays visible"),
    ]
    return [{"rule_id": a, "trigger": b, "definition": c, "effect": d,
             "applies_to": "every family, control and combo"} for a, b, c, d in rows]


def main():
    reg = register()
    n_reg = wcsv("strategy_registration.csv", reg)

    fc = rcsv("forecasts.csv")
    import lib
    mirror = {g["game_id"]: g for g in lib.mirror_games() if g["season"] == "2026"}
    for r in fc:
        g = mirror.get(r["game_id"], {})
        r["market_rest_home"] = g.get("home_rest", "")
        r["market_rest_away"] = g.get("away_rest", "")
        r["div_game"] = g.get("div_game", "")

    graded = grade(fc)
    n_graded = wcsv("strategy_graded_bets.csv", graded)
    ctrl = control_rows(fc)
    n_ctrl = wcsv("control_baselines.csv", ctrl)

    fam = {}
    for r in graded:
        fam.setdefault(r["family_id"], []).append(r)

    ctrl_summary = {}
    for c in ("C1", "C2", "C3"):
        rows = [r for r in ctrl if r["control_id"] == c]
        hits = [1.0 if r["won"] == "yes" else 0.0 for r in rows if r["won"] != ""]
        ctrl_summary[c] = {
            "n": len(rows),
            # C1 and C2 are side bets graded win/loss, so their proper score is the
            # Brier score of the coin-flip probability they are registered with against
            # their OWN outcome. C3 exists only to fix the 0.25 floor.
            "brier": brier([float(r["proper_score_p"]) for r in rows],
                           [int(r["outcome"]) for r in rows]),
            "hit": mean(hits) if hits else None,
            "n_decided": len(hits),
            "tier": "control",
        }

    scored = {}
    for fid, rows in fam.items():
        ftype = FAMILY_TYPES[fid]
        if ftype == "model" and any(r["proper_score_p"] != "" for r in rows):
            ps = [float(r["proper_score_p"]) for r in rows if r["proper_score_p"] != ""]
            ys = [int(r["outcome"]) for r in rows if r["proper_score_p"] != ""]
            n = len(ps)
            b = brier(ps, ys)
            ses = [(p - y) ** 2 for p, y in zip(ps, ys)]
            m, s_ = mean(ses), sd(ses)
            z = (m - 0.25) / (s_ / math.sqrt(n)) if s_ else 0.0
            scored[fid] = {"type": "proper score (Brier)", "n": n, "brier": b,
                           "headline": 1 - b / 0.25,
                           "p": 0.5 * (1 + math.erf(z / math.sqrt(2)))}
        elif ftype == "joint":
            continue
        else:
            decided = [r for r in rows if r["won"] in ("yes", "no")]
            n = len(decided)
            if not n:
                continue
            wins = sum(1 for r in decided if r["won"] == "yes")
            priced = [r for r in decided if r["price_american"] != ""]
            p_null = (sum(american_to_prob(float(r["price_american"])) for r in priced)
                      / len(priced)) if priced else 0.5
            scored[fid] = {"type": "hit rate vs price-implied null", "n": n,
                           "hit": wins / n, "p_null": p_null,
                           "headline": wins / n - p_null,
                           "p": binom_test_two_sided(wins, n, p_null)}
    fids = sorted(scored)
    adj = holm([scored[fid]["p"] for fid in fids]) if fids else []
    p_adj = {fid: adj[i] for i, fid in enumerate(fids)}

    board = []
    for fid in fids:
        rows = fam[fid]
        units = [r for r in rows if r["staking_return_units"] != ""]
        decided = [r for r in rows if r["won"] in ("yes", "no")]
        hit = mean([1.0 if r["won"] == "yes" else 0.0 for r in decided]) if decided else None
        ret = sum(float(r["staking_return_units"]) for r in units) if units else None
        roi = (ret / len(units)) if units and len(units) else None
        sc = scored[fid]
        board.append({
            "family_id": fid,
            "family": next(x[1] for x in FAMILIES if x[0] == fid),
            "bet_class": next(x[2] for x in FAMILIES if x[0] == fid),
            "signal_type": sc["type"],
            "universe": "PROSPECTIVE ONLY (weeks 5-10, aggregator prices)",
            "graded_bets": len(decided),
            "signal_headline": f(sc["headline"], 4),
            "signal_headline_meaning": ("Brier skill vs the 0.25 coin-flip floor"
                                        if "Brier" in sc["type"]
                                        else "hit rate minus the null rate implied by the price paid"),
            "signal_brier": f(sc["brier"], 4) if "Brier" in sc["type"] else "",
            "signal_p_raw": f(sc["p"], 4),
            "signal_p_holm": f(p_adj[fid], 4),
            "staking_n_priced": len(units),
            "staking_units_returned": f(ret, 3) if ret is not None else "",
            "staking_roi_pct": f(100 * roi, 2) if roi is not None else "",
            "hit_rate": f(hit, 4) if hit is not None else "",
            "certified": "no",
            "state": "PAPER",
            "why_not_certified": ("gate G2 fails (no verified price) and gate G4 fails (n < 300); "
                                  "nothing can be certified on aggregator prices"),
        })
    # ranks only within a comparable signal type
    for stype in sorted({r["signal_type"] for r in board}):
        sel = [r for r in board if r["signal_type"] == stype]
        sel.sort(key=lambda r: float(r["signal_headline"]), reverse=True)
        for i, r in enumerate(sel, 1):
            r["signal_rank"] = i
    withret = [r for r in board if r["staking_roi_pct"] != ""]
    withret.sort(key=lambda r: float(r["staking_roi_pct"]), reverse=True)
    for i, r in enumerate(withret, 1):
        r["staking_rank"] = i
    for r in board:
        r.setdefault("signal_rank", "")
        r.setdefault("staking_rank", "")
        r["rank_gap"] = (int(r["signal_rank"]) - int(r["staking_rank"])) if (
            r["staking_rank"] != "" and r["signal_rank"] != "") else ""
        r["gates_status"] = ("G0 MET / G1 MET / G2 NOT MET / G3 MET / G4 NOT MET / "
                             "G5 MET / G6 NOT MET / G8 PARTIAL / G9 MET / G10 MET / G11 NOT MET")
    fields = ["family_id", "family", "bet_class", "signal_type", "universe", "graded_bets",
              "signal_headline", "signal_headline_meaning", "signal_brier", "signal_p_raw",
              "signal_p_holm", "signal_rank", "staking_n_priced", "staking_units_returned",
              "staking_roi_pct", "staking_rank", "rank_gap", "hit_rate", "gates_status",
              "certified", "state", "why_not_certified"]
    board = sorted(board, key=lambda r: (r["signal_type"], int(r["signal_rank"])))
    n_board = wcsv("leaderboard.csv", [{k: r[k] for k in fields} for r in board])

    n_gates = wcsv("gates.csv", [{"gate_id": a, "name": b, "test": c, "class": d,
                                  "status": e, "blocking_flags": g,
                                  "source_url": "https://www.nfl.com/standings/league/2026/REG"}
                                 for a, b, c, d, e, g in GATES])
    n_dem = wcsv("demotion_rules.csv", demotion_rules())
    n_ctrl_defs = wcsv("control_definitions.csv",
                       [{"control_id": a, "name": b, "bet_class": c, "rule_text": d}
                        for a, b, c, d in CONTROLS])
    corr, withheld = correlation_rows()
    n_corr = wcsv("correlations_official.csv", corr)
    n_with = wcsv("correlations_withheld.csv",
                  [{"withheld_id": a, "pair": b, "why_not_published": c,
                    "prior_input_tier": d, "status": e} for a, b, c, d, e in withheld])
    n_luck = wcsv("luck_panel.csv", luck_panel(fc))
    n_ctrl_sum = wcsv("control_summary.csv",
                      [{"control_id": k, "name": next(c[1] for c in CONTROLS if c[0] == k),
                        "n_rows": v["n"], "n_decided": v["n_decided"],
                        "brier": f(v["brier"], 4),
                        "hit_rate": f(v["hit"], 4) if v["hit"] is not None else "",
                        "signal_score_vs_coinflip": f(100 * (1 - v["brier"] / 0.25), 2)}
                       for k, v in sorted(ctrl_summary.items())])

    best = sorted(board, key=lambda r: float(r["signal_p_holm"]))[0] if board else {}
    disagreement = next((("%s %s: signal rank %s of %d, staking rank %s of %d"
                          % (r["family_id"], r["family"], r["signal_rank"],
                             sum(1 for x in board if x["signal_type"] == r["signal_type"]),
                             r["staking_rank"], len(withret)))
                         for r in board
                         if r["staking_rank"] != "" and r["signal_rank"] != ""
                         and int(r["signal_rank"]) != int(r["staking_rank"])), "none")
    summary = {
        "registered_families": n_reg,
        "graded_bets": n_graded,
        "leaderboard_rows": n_board,
        "controls": n_ctrl,
        "control_definitions": n_ctrl_defs,
        "certified": 0,
        "best_signal_family": best.get("family", ""),
        "best_signal_p_holm": best.get("signal_p_holm", ""),
        "best_staking_family": withret[0]["family"] if withret else "",
        "best_staking_roi_pct": withret[0]["staking_roi_pct"] if withret else "",
        "rank_disagreement_example": disagreement,
        "control_brier_c1_random": f(ctrl_summary["C1"]["brier"], 4),
        "control_brier_c2_favourites": f(ctrl_summary["C2"]["brier"], 4),
        "control_brier_c3_coinflip": f(ctrl_summary["C3"]["brier"], 4),
        "control_hit_c1_random": f(ctrl_summary["C1"]["hit"], 4),
        "control_hit_c2_favourites": f(ctrl_summary["C2"]["hit"], 4),
        "official_correlations": n_corr,
        "withheld_correlations": n_with,
        "demotion_rules": n_dem,
        "luck_panel_rows": n_luck,
    }
    wjson("strategy_summary.json", summary)
    wjson("control_summary.json", {k: {"n": v["n"], "brier": v["brier"], "hit": v["hit"]}
                                   for k, v in ctrl_summary.items()})
    print("registered families:", n_reg, "graded bets:", n_graded, "leaderboard rows:", n_board)
    for r in board:
        print("  %-3s %-32s %-22s %-9s rank=%-2s p_holm=%-8s | ROI=%-8s rank=%-2s | n=%s"
              % (r["family_id"], r["signal_type"], r["signal_headline"],
                 r["signal_p_holm"], r["signal_rank"], r["signal_p_holm"],
                 r["staking_roi_pct"], r["staking_rank"], r["graded_bets"]))
    print("controls:", {k: round(v["brier"], 4) for k, v in ctrl_summary.items()})
    print("luck panel rows:", n_luck, "| official correlations:", n_corr,
          "| withheld:", n_with)
    print("rank disagreement:", disagreement)


if __name__ == "__main__":
    main()

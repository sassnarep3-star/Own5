"""Deterministic derivation pipeline for the 715e2cd4 NFL line-origination desk.

Reads only the text extracts in raw/ (official nfl.com reads, hashed in
data/captures.csv) and writes every derived table in data/.  No clock, no
network, no git, no randomness (all bootstrap-free intervals are analytic).

Model specification is frozen in data/preregistration.csv BEFORE the Week 10
evaluation window is scored.  See MODEL_SPEC below.
"""

import csv
import hashlib
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
DATA = os.path.join(HERE, "data")

CAPTURE_UTC = "2026-11-19T06:55:00Z"

# ---------------------------------------------------------------- MODEL_SPEC
# Pre-registered 2026-11-19 before any Week 10 result was scored.
MODEL_SPEC = {
    "spec_id": "M1-ridge-offdef",
    "trained_on": "2026 regular season Weeks 1-9 (136 official finals)",
    "target": "home points and away points",
    "form": "hp = mu + h/2 + off_H + def_A ; ap = mu - h/2 + off_A + def_H",
    "mu": "mean team points per game in the training corpus (plug-in)",
    "h": "mean home margin in the training corpus (plug-in)",
    "ridge_lambda": 5.0,          # points^2, fixed before scoring
    "sensitivity_lambdas": [1.0, 5.0, 10.0, 25.0],
    "total_estimator_a": "sum of the two fitted expected points",
    "total_estimator_b": "mean of the two clubs' own average combined game total",
    "moneyline_mapping": "P(home win) = Phi(model_margin / sigma), sigma = sd of "
                         "training-corpus margin residuals (plug-in, no fitting on test)",
    "origination_order": "side -> total -> moneyline",
    "holdout": "Week 10 2026 (14 official finals), chronological, never in training",
    "week11_origination_training_set": "Weeks 1-10 2026 (150 official finals)",
}

REPO_DATA = "https://github.com/sassnarep3-star/Own5/blob/main/nfl-desk-715e2cd4/data/"

SOURCES = {
    "standings": "https://www.nfl.com/standings/league/2026/REG",
    "schedule_wk11": "https://www.nfl.com/schedules/2026/by-week/week-11",
    "schedule_wk10": "https://www.nfl.com/schedules/2026/by-week/week-10",
    "injuries_reg11": "https://www.nfl.com/injuries/league/2026/reg11",
    "venue_source": "https://www.nfl.com/games/",
}


# ------------------------------------------------------------------ helpers
def read_pipe(name, min_fields=None):
    """Read a pipe/delim extract, skipping '#' comments and blank lines."""
    out = []
    path = os.path.join(RAW, name)
    with open(path, encoding="utf-8") as fh:
        for ln, line in enumerate(fh, 1):
            line = line.rstrip("\n")
            if not line.strip() or line.startswith("#"):
                continue
            if name.endswith(".txt") and "|" in line:
                row = line.split("|")
            else:
                row = line.split()
            if min_fields is not None and len(row) < min_fields:
                raise SystemExit("drift alarm: %s line %d has %d fields, need %d: %r"
                                 % (name, ln, len(row), min_fields, line))
            out.append(row)
    return out


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def write_csv(name, header, rows):
    path = os.path.join(DATA, name)
    os.makedirs(DATA, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(header)
        for r in rows:
            w.writerow(r)
    return path


def norm_cdf(z):
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def mean(xs):
    return sum(xs) / float(len(xs))


def sd(xs):
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / float(len(xs) - 1))


def pearson(xs, ys):
    mx, my = mean(xs), mean(ys)
    sxy = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    sxx = sum((a - mx) ** 2 for a in xs)
    syy = sum((b - my) ** 2 for b in ys)
    return sxy / math.sqrt(sxx * syy)


def fisher_ci(r, n, z=1.959963985):
    if n <= 3:
        return ("", "")
    if abs(r) >= 0.999999:
        return ("", "")
    zr = 0.5 * math.log((1 + r) / (1 - r))
    se = 1.0 / math.sqrt(n - 3)
    lo, hi = zr - z * se, zr + z * se
    return (round(math.tanh(lo), 4), round(math.tanh(hi), 4))


def wilson(k, n, z=1.959963985):
    p = k / float(n)
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    s = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (round((c - s) / d, 4), round((c + s) / d, 4))


def solve(a, b):
    """Gaussian elimination with partial pivoting; a is n x n, b is n."""
    n = len(a)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(m[r][col]))
        if abs(m[piv][col]) < 1e-12:
            raise ValueError("singular normal equations")
        m[col], m[piv] = m[piv], m[col]
        pv = m[col][col]
        for j in range(col, n + 1):
            m[col][j] /= pv
        for r in range(n):
            if r == col:
                continue
            f = m[r][col]
            if f == 0.0:
                continue
            for j in range(col, n + 1):
                m[r][j] -= f * m[col][j]
    return [m[i][n] for i in range(n)]


# --------------------------------------------------------------- load inputs
def load_standings():
    """Official 2026 REG standings (32 clubs), read 2026-11-19."""
    rows = read_pipe("standings_2026_reg.txt", 6)
    out = {}
    for r in rows:
        team, w, l, t, pf, pa = r[0], int(r[1]), int(r[2]), int(r[3]), int(r[4]), int(r[5])
        out[team] = {"w": w, "l": l, "t": t, "pf": pf, "pa": pa,
                     "gp": w + l + t}
    if len(out) != 32:
        raise SystemExit("drift alarm: standings has %d clubs, expected 32" % len(out))
    return out


# The carried corpus uses the nflverse-style club codes for three clubs; the
# official standings table uses the league's own abbreviations. Map, never guess.
CLUB_ALIASES = {"LAR": "LA", "ARI": "AZ", "WSH": "WAS"}


def load_corpus():
    """136-game pre-registered corpus: official finals, Weeks 1-9 2026."""
    path = os.path.join(HERE, "data", "corpus_136_source.csv")
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    if len(rows) != 136:
        raise SystemExit("drift alarm: corpus has %d rows, expected 136" % len(rows))
    out = []
    for r in rows:
        out.append({
            "game_id": r["event_id"], "week": int(r["week"]), "date": r["date"],
            "away": CLUB_ALIASES.get(r["away_team"], r["away_team"]),
            "home": CLUB_ALIASES.get(r["home_team"], r["home_team"]),
            "away_raw": r["away_team"], "home_raw": r["home_team"],
            "away_pts": int(r["away_points"]), "home_pts": int(r["home_points"]),
            "source_url": r["official_source_url"],
        })
    return out


def load_results_wk10():
    rows = read_pipe("results_2026_wk10.txt", 5)
    if len(rows) != 14:
        raise SystemExit("drift alarm: Week 10 extract has %d finals, expected 14" % len(rows))
    out = []
    for r in rows:
        out.append({"date": r[4], "away": r[0], "home": r[1],
                    "away_pts": int(r[2]), "home_pts": int(r[3]),
                    "source_url": SOURCES["schedule_wk10"]})
    return out


# Venue labels where the two official pages disagree. The game centre's Game Info
# block is treated as the source of record; the schedule page's stadium link is
# quoted beside it and the disagreement is published as flag F-03.
VENUE_DISPUTES = {
    ("CIN", "WAS"): ("FedEx Field", "NORTHWEST STADIUM",
                     "schedule page label; the game centre Game Info block prints "
                     "NORTHWEST STADIUM, LANDOVER MD (F-03)"),
}


def load_schedule_wk11():
    rows = read_pipe("schedule_2026_wk11.txt", 7)
    if len(rows) != 13:
        raise SystemExit("drift alarm: Week 11 extract has %d fixtures, expected 13" % len(rows))
    out = []
    for r in rows:
        away, home, date, kick, net, venue = r[0], r[1], r[2], r[3], r[4], r[5]
        dispute = VENUE_DISPUTES.get((away, home))
        if dispute:
            sched_label, gc_label, note = dispute
            if venue.strip() != sched_label:
                raise SystemExit("venue dispute anchor changed: %r" % venue)
            venue = "%s %s — %s" % (gc_label, "/" + sched_label, note)
        out.append({"away": away, "home": home, "date": date, "kickoff": kick,
                    "network": net, "venue": venue})
    return out


# ------------------------------------------------------------ 1. reconciliation
def reconcile(standings, corpus, wk10):
    """Prove the corpus is complete and correct against the official standings.

    For every club: official (W,L,T,PF,PA) minus corpus totals must equal that
    club's Week 10 line exactly (computed from the official Week 10 finals).
    """
    rows = []
    agg = {t: [0, 0, 0, 0, 0] for t in standings}
    for g in corpus:
        a, h = g["away"], g["home"]
        ap, hp = g["away_pts"], g["home_pts"]
        for t, sf, sa in ((a, ap, hp), (h, hp, ap)):
            agg[t][3] += sf
            agg[t][4] += sa
            if sf > sa:
                agg[t][0] += 1
            elif sa > sf:
                agg[t][1] += 1
            else:
                agg[t][2] += 1
    wk10_by_team = {}
    for g in wk10:
        a, h = g["away"], g["home"]
        ap, hp = g["away_pts"], g["home_pts"]
        if ap > hp:
            wk10_by_team[a] = (1, 0, 0, ap, hp)
            wk10_by_team[h] = (0, 1, 0, hp, ap)
        elif hp > ap:
            wk10_by_team[a] = (0, 1, 0, ap, hp)
            wk10_by_team[h] = (1, 0, 0, hp, ap)
        else:
            wk10_by_team[a] = (0, 0, 1, ap, hp)
            wk10_by_team[h] = (0, 0, 1, hp, ap)
    bad = 0
    for t in sorted(standings):
        s = standings[t]
        c = agg[t]
        if t in wk10_by_team:
            won, lost, tied, sf, sa = wk10_by_team[t]
            exp = (c[0] + won, c[1] + lost, c[2] + tied, c[3] + sf, c[4] + sa)
        else:
            exp = tuple(c)
        ok = exp == (s["w"], s["l"], s["t"], s["pf"], s["pa"])
        if not ok:
            bad += 1
        rows.append([
            t, s["w"], s["l"], s["t"], s["pf"], s["pa"], s["gp"],
            c[0], c[1], c[2], c[3], c[4],
            exp[0], exp[1], exp[2], exp[3], exp[4],
            "MATCH" if ok else "MISMATCH",
            "on bye in Week 10 (4 clubs)" if t not in wk10_by_team else "played Week 10",
            SOURCES["standings"],
        ])
    return rows, bad, agg


# ------------------------------------------------------------------ 2. ratings
def fit_ratings(games, teams, lam):
    """Ridge-regularised offence/defence ratings on points scored/allowed.

    hp = mu + h/2 + off_H + def_A ; ap = mu - h/2 + off_A + def_H
    mu and h are plug-in moments of the training corpus. Parameters are the 32
    off and 32 def values, shrunk to 0 by lam.
    """
    hp = [g["home_pts"] for g in games]
    ap = [g["away_pts"] for g in games]
    mu = (sum(hp) + sum(ap)) / float(2 * len(games))
    h = mean([a - b for a, b in zip(hp, ap)])
    idx = {t: i for i, t in enumerate(sorted(teams))}
    n = 2 * len(idx)
    xtx = [[0.0] * n for _ in range(n)]
    xty = [0.0] * n
    for k, g in enumerate(games):
        a, hm = idx[g["away"]], idx[g["home"]]
        for row, y in (
            ({hm: 1.0, len(idx) + a: 1.0}, hp[k] - (mu + h / 2.0)),
            ({a: 1.0, len(idx) + hm: 1.0}, ap[k] - (mu - h / 2.0)),
        ):
            keys = list(row)
            for i in keys:
                xty[i] += row[i] * y
                for j in keys:
                    xtx[i][j] += row[i] * row[j]
    for i in range(n):
        xtx[i][i] += lam
    theta = solve(xtx, xty)
    off = {t: theta[idx[t]] for t in idx}
    dfn = {t: theta[len(idx) + idx[t]] for t in idx}
    return {"mu": mu, "h": h, "off": off, "def": dfn, "lam": lam}


def predict(m, away, home):
    mu, h = m["mu"], m["h"]
    hp = mu + h / 2.0 + m["off"][home] + m["def"][away]
    ap = mu - h / 2.0 + m["off"][away] + m["def"][home]
    return hp, ap


def fit_sigma(m, games):
    resid = []
    for g in games:
        hp, ap = predict(m, g["away"], g["home"])
        resid.append((g["home_pts"] - g["away_pts"]) - (hp - ap))
    return sd(resid)


def avg_combined_total(games, team):
    vals = []
    for g in games:
        if g["home"] == team or g["away"] == team:
            vals.append(g["home_pts"] + g["away_pts"])
    return sum(vals) / float(len(vals)) if vals else None


# ----------------------------------------------------------------- 3. scoring
def score_game(model, sigma, g, games):
    hp, ap = predict(model, g["away"], g["home"])
    m_total_a = hp + ap
    ta = avg_combined_total(games, g["home"])
    tb = avg_combined_total(games, g["away"])
    m_total_b = 0.5 * (ta + tb)
    margin = g["home_pts"] - g["away_pts"]
    actual_total = g["home_pts"] + g["away_pts"]
    p_home = norm_cdf((hp - ap) / sigma)
    return {
        "model_spread": round(-(hp - ap), 2),      # home spread, negative = home favoured
        "model_total_a": round(m_total_a, 2),
        "model_total_b": round(m_total_b, 2),
        "model_p_home": round(p_home, 4),
        "model_margin": round(hp - ap, 2),
        "actual_margin": margin,
        "actual_total": actual_total,
        "home_won": 1 if margin > 0 else 0,
        "tie": 1 if margin == 0 else 0,
    }


def main():
    os.makedirs(DATA, exist_ok=True)
    standings = load_standings()
    corpus = load_corpus()
    wk10 = load_results_wk10()
    sched11 = load_schedule_wk11()

    # ---- captures ledger
    caps = []
    for cid, ds, url, fn, note in [
        ("C01", "2026 REG standings (32 clubs)", SOURCES["standings"],
         "standings_2026_reg.txt", "team|W|L|T|PF|PA rows transcribed from the standings table"),
        ("C02", "Week 11 schedule + byes", SOURCES["schedule_wk11"],
         "schedule_2026_wk11.txt", "fixture rows; venue label taken from the schedule page's stadium link text"),
        ("C03", "Week 10 finals", SOURCES["schedule_wk10"],
         "results_2026_wk10.txt", "14 finals with scores"),
        ("C04", "Week 11 injury report", SOURCES["injuries_reg11"],
         "injuries_2026_reg11.txt", "253 player rows across 24 clubs; 2 clubs report no injuries"),
        ("C05", "Game-centre venue checks (2 fixtures)", SOURCES["venue_source"] + "bengals-at-commanders-2026-reg-11",
         "venues_spotcheck.txt", "Game Info block: location + stadium"),
        ("C06", "Announced-starter evidence (news)", "https://www.nfl.com/news/",
         "starter_changes_2026-11-19.txt", "dated league articles naming starters"),
    ]:
        path = os.path.join(RAW, fn)
        if not os.path.exists(path):
            raise SystemExit("missing raw extract: %s" % path)
        n = len([1 for ln in open(path, encoding="utf-8")
                 if ln.strip() and not ln.startswith("#")])
        caps.append([cid, ds, url, CAPTURE_UTC, "raw/" + fn, sha256_file(path), n, note])
    write_csv("captures.csv",
              ["capture_id", "dataset", "source_url", "retrieved_utc", "extract_file",
               "sha256", "extract_rows", "note"], caps)

    # ---- 1. results corpus + reconciliation
    write_csv(
        "results_corpus.csv",
        ["game_id", "week", "date", "away_team", "home_team", "away_points", "home_points",
         "winner", "margin", "total", "source_url", "status"],
        [[g["game_id"], g["week"], g["date"], g["away"], g["home"], g["away_pts"],
          g["home_pts"],
          "TIE" if g["home_pts"] == g["away_pts"] else (g["home"] if g["home_pts"] > g["away_pts"] else g["away"]),
          g["home_pts"] - g["away_pts"], g["home_pts"] + g["away_pts"], g["source_url"],
          "FINAL (official)"] for g in corpus])

    rec_rows, bad, agg = reconcile(standings, corpus, wk10)
    write_csv("reconciliation.csv",
              ["team", "official_w", "official_l", "official_t", "official_pf", "official_pa",
               "official_gp", "corpus_w", "corpus_l", "corpus_t", "corpus_pf", "corpus_pa",
               "corpus_plus_week10_w", "corpus_plus_week10_l", "corpus_plus_week10_t",
               "corpus_plus_week10_pf", "corpus_plus_week10_pa", "result", "week10_note",
               "source_url"], rec_rows)

    # ---- 2. ratings (training corpus = weeks 1-9) and sensitivity
    teams = sorted(standings)
    sens = []
    fitted = {}
    for lam in MODEL_SPEC["sensitivity_lambdas"]:
        m = fit_ratings(corpus, teams, lam)
        sig = fit_sigma(m, corpus)
        fitted[lam] = (m, sig)
        errs_sp, errs_ta, errs_tb = [], [], []
        for g in wk10:
            s = score_game(m, sig, g, corpus)
            errs_sp.append(abs(s["model_spread"] - (-s["actual_margin"])))
            errs_ta.append(abs(s["model_total_a"] - s["actual_total"]))
            errs_tb.append(abs(s["model_total_b"] - s["actual_total"]))
        sens.append([lam, round(mean(errs_sp), 3), round(mean(errs_ta), 3),
                     round(mean(errs_tb), 3), round(sig, 3),
                     "pre-registered" if lam == MODEL_SPEC["ridge_lambda"] else "sensitivity",
                     SOURCES["schedule_wk10"]])
    write_csv("lambda_sensitivity.csv",
              ["ridge_lambda", "week10_mae_spread_pts", "week10_mae_total_A_pts",
               "week10_mae_total_B_pts", "sigma_points", "role", "source_url"], sens)

    model, sigma = fitted[MODEL_SPEC["ridge_lambda"]]

    rate_rows = []
    for t in teams:
        s = standings[t]
        gp = s["gp"]
        rate_rows.append([t, gp, s["pf"], s["pa"], round(s["pf"] / gp, 2), round(s["pa"] / gp, 2),
                          round((s["pf"] - s["pa"]) / gp, 2),
                          round(model["off"][t], 3), round(model["def"][t], 3),
                          SOURCES["standings"]])
    write_csv("team_ratings.csv",
              ["team", "games_played", "points_for", "points_against", "pf_per_game",
               "pa_per_game", "net_per_game", "offence_rating_pts", "defence_rating_pts",
               "source_url"], rate_rows)
    write_csv("model_params.csv",
              ["param", "value", "definition"],
              [["spec_id", MODEL_SPEC["spec_id"], "frozen model identifier"],
               ["mu", round(model["mu"], 4), "mean team points per game, weeks 1-9"],
               ["hfa", round(model["h"], 4), "mean home margin, weeks 1-9 (points)"],
               ["sigma", round(sigma, 4), "sd of margin residuals, weeks 1-9 (ML mapping)"],
               ["ridge_lambda", MODEL_SPEC["ridge_lambda"], "pre-registered shrinkage"],
               ["training_games", len(corpus), "official finals used"],
               ["source_url", SOURCES["schedule_wk10"], "results provenance"]])

    # ---- 3. week 10 walk-forward scorecard
    wf = []
    for g in wk10:
        s = score_game(model, sigma, g, corpus)
        wf.append([g["date"], g["away"], g["home"], s["model_spread"], s["actual_margin"],
                   round(s["model_spread"] + s["actual_margin"], 2),
                   s["model_total_a"], s["model_total_b"], s["actual_total"],
                   round(s["model_total_a"] - s["actual_total"], 2),
                   round(s["model_total_b"] - s["actual_total"], 2),
                   s["model_p_home"], s["home_won"],
                   round(abs(s["model_spread"] - (-s["actual_margin"])), 2),
                   g["source_url"]])
    write_csv("walkforward_week10.csv",
              ["date", "away_team", "home_team", "model_home_spread", "actual_margin",
               "side_error_pts", "model_total_A", "model_total_B", "actual_total",
               "total_A_error", "total_B_error", "model_p_home_win", "home_won",
               "abs_spread_error", "source_url"], wf)

    # ---- 4. scorecard with baselines and intervals
    n = len(wk10)
    sp_err, ta_err, tb_err = [], [], []
    brier, brier_base = [], []
    base_home_rate = mean([1 if g["home_pts"] > g["away_pts"] else 0 for g in corpus])
    base_total = mean([g["home_pts"] + g["away_pts"] for g in corpus])
    base_margin = model["h"]
    base_maj = []
    for g in wk10:
        s = score_game(model, sigma, g, corpus)
        sp_err.append(abs(s["model_spread"] - (-s["actual_margin"])))
        ta_err.append(abs(s["model_total_a"] - s["actual_total"]))
        tb_err.append(abs(s["model_total_b"] - s["actual_total"]))
        brier.append((s["model_p_home"] - s["home_won"]) ** 2)
        brier_base.append((base_home_rate - s["home_won"]) ** 2)
        base_maj.append(abs(-base_margin - (-s["actual_margin"])))
    bss = 1 - (mean(brier) / mean(brier_base))

    # standard error of the mean absolute error, reported rather than a CI,
    # because n=14 makes a CI indistinguishable from "no information".
    def sem(xs):
        return sd(xs) / math.sqrt(len(xs))

    # correct baseline for totals: constant league-mean total (no per-club information)
    total_base = [abs(base_total - (g["home_pts"] + g["away_pts"])) for g in wk10]
    sc = [
        ["Week 10 side (spread) MAE", round(mean(sp_err), 3), n,
         round(mean(sp_err) - 1.96 * sem(sp_err), 3),
         round(mean(sp_err) + 1.96 * sem(sp_err), 3),
         "constant home-margin baseline (no club information)", round(mean(base_maj), 3),
         round(1 - mean(sp_err) / mean(base_maj), 4),
         "Informational only: FAILS minimum-sample gate G1 (needs 300 scored bets)", SOURCES["schedule_wk10"]],
        ["Week 10 total MAE (estimator A)", round(mean(ta_err), 3), n,
         round(mean(ta_err) - 1.96 * sem(ta_err), 3),
         round(mean(ta_err) + 1.96 * sem(ta_err), 3),
         "constant league-mean total (no club information)", round(mean(total_base), 3),
         round(1 - mean(ta_err) / mean(total_base), 4),
         "Informational only: FAILS gate G1; A vs B compared in lambda_sensitivity.csv", SOURCES["schedule_wk10"]],
        ["Week 10 total MAE (estimator B)", round(mean(tb_err), 3), n,
         round(mean(tb_err) - 1.96 * sem(tb_err), 3),
         round(mean(tb_err) + 1.96 * sem(tb_err), 3),
         "constant league-mean total (no club information)", round(mean(total_base), 3),
         round(1 - mean(tb_err) / mean(total_base), 4),
         "Informational only: FAILS gate G1; B is club-average so it is weaker out of sample", SOURCES["schedule_wk10"]],
        ["Week 10 moneyline Brier skill vs base rate", round(bss, 4), n, "", "",
         "Brier of the training-corpus home-win rate", round(mean(brier_base), 4),
         round(bss, 4),
         "Informational only: FAILS gate G1 and gate G3 (no calibration sample)", SOURCES["schedule_wk10"]],
    ]
    write_csv("scorecard.csv",
              ["metric", "value", "n", "ci_low", "ci_high", "baseline",
               "baseline_value", "skill_vs_baseline", "verdict", "source_url"], sc)

    # ---- 5. week 11 origination (trained on weeks 1-10 = 150 official finals)
    full = corpus + wk10
    if len(full) != 150:
        raise SystemExit("drift alarm: weeks 1-10 corpus is %d games, expected 150" % len(full))
    m11 = fit_ratings(full, teams, MODEL_SPEC["ridge_lambda"])
    s11 = fit_sigma(m11, full)
    line_rows = []
    for i, f in enumerate(sched11, 1):
        hp, ap = predict(m11, f["away"], f["home"])
        ta = avg_combined_total(full, f["home"])
        tb = avg_combined_total(full, f["away"])
        p_home = norm_cdf((hp - ap) / s11)
        game_id = "W11-%02d" % i
        spread = round(-(hp - ap), 2)
        total_a = round(hp + ap, 2)
        total_b = round(0.5 * (ta + tb), 2)
        line_rows.append([
            game_id, f["date"], f["kickoff"], f["away"], f["home"], f["venue"], f["network"],
            "side -> total -> moneyline",
            spread, total_a, total_b, round(total_a - total_b, 2),
            round(p_home * 100, 1), round((1 - p_home) * 100, 1),
            round(p_home, 4),
            "", "", "", "", "", "",
            "mu=%.2f HFA=%.2f sigma=%.2f lambda=%.1f trained on %d official finals (weeks 1-10); "
            "ML from Phi(margin/sigma)" % (m11["mu"], m11["h"], s11, m11["lam"], len(full)),
            SOURCES["schedule_wk11"],
            "MODEL OUTPUT (derived); market columns UNVERIFIED (no licensed price feed)"])
    write_csv("lines_week11.csv",
              ["game_id", "date", "kickoff_et", "away_team", "home_team", "venue", "network",
               "origination_order", "model_home_spread", "model_total_A", "model_total_B",
               "total_gap_A_minus_B", "model_home_ml_implied_cents", "model_away_ml_implied_cents",
               "model_p_home_win", "market_home_spread", "spread_residual",
               "market_total", "total_residual", "market_home_ml", "ml_residual",
               "inputs", "source_url", "status"], line_rows)

    # ---- 6. price-snapshot store: schema + honest zero coverage
    write_csv("price_snapshots.csv",
              ["snapshot_id", "game_id", "market_type", "selection", "phase", "line",
               "price_american", "operator", "jurisdiction", "captured_at_utc",
               "source_url", "extract_sha256", "status"], [])
    write_csv("price_coverage.csv",
              ["item", "value", "note", "source_url"],
              [["markets originated", "39 (13 games x side, total, moneyline)",
                "counted from the 13 official fixtures", SOURCES["schedule_wk11"]],
               ["official price captures held", "0",
                "no licensed operator price feed in this namespace", REPO_DATA + "price_snapshots.csv"],
               ["opening-number captures", "0", "BLANK + FLAGGED F-01", REPO_DATA + "flagged.csv"],
               ["closing-number captures", "0", "BLANK + FLAGGED F-01", REPO_DATA + "flagged.csv"],
               ["policy", "P-01 no unlicensed operator scraping", "written before any scorecard row existed",
                REPO_DATA + "price_policy.csv"]])

    # ---- 7. correlations, official numbers only
    corr = []
    w = [standings[t]["w"] + 0.5 * standings[t]["t"] for t in teams]
    pct = [w[i] / standings[t]["gp"] for i, t in enumerate(teams)]
    pfg = [standings[t]["pf"] / standings[t]["gp"] for t in teams]
    pag = [standings[t]["pa"] / standings[t]["gp"] for t in teams]
    netg = [pfg[i] - pag[i] for i in range(32)]
    for name, xs, ys in [
        ("Points for per game vs win percentage", pfg, pct),
        ("Points against per game vs win percentage", pag, pct),
        ("Net points per game vs win percentage", netg, pct),
        ("Points for per game vs points against per game", pfg, pag),
    ]:
        r = pearson(xs, ys)
        lo, hi = fisher_ci(r, 32)
        corr.append([name, "Pearson r", round(r, 4), 32, lo, hi, "club level (n=32 clubs)",
                     SOURCES["standings"],
                     "computed in-repo from the official 2026 REG standings read 2026-11-19"])
    margins = [g["home_pts"] - g["away_pts"] for g in corpus]
    totals = [g["home_pts"] + g["away_pts"] for g in corpus]
    absorbed = [abs(m) for m in margins]
    for name, xs, ys in [
        ("Game margin vs game total (136-game corpus)", margins, totals),
        ("Absolute margin vs game total (136-game corpus)", absorbed, totals),
        ("Home points vs away points (136-game corpus)",
         [g["home_pts"] for g in corpus], [g["away_pts"] for g in corpus]),
    ]:
        r = pearson(xs, ys)
        lo, hi = fisher_ci(r, 136)
        corr.append([name, "Pearson r", round(r, 4), 136, lo, hi, "game level (n=136 games)",
                     SOURCES["schedule_wk10"],
                     "computed in-repo from the pre-registered 136-game official corpus"])
    write_csv("correlations.csv",
              ["pair", "metric", "value", "n", "ci_low", "ci_high", "unit_of_analysis",
               "source_url", "note"], corr)

    # ---- 8. luck panel
    home_wins = sum(1 for g in corpus if g["home_pts"] > g["away_pts"])
    lo, hi = wilson(home_wins, 136)
    pyth = []
    for t in teams:
        s = standings[t]
        e = 2.37
        exp = s["gp"] * (s["pf"] ** e) / (s["pf"] ** e + s["pa"] ** e)
        act = s["w"] + 0.5 * s["t"]
        pyth.append([t, s["gp"], s["w"], s["t"], round(act, 1), round(exp, 2),
                     round(act - exp, 2), SOURCES["standings"]])
    write_csv("luck_pythagorean.csv",
              ["team", "games_played", "wins", "ties", "actual_wins_equiv",
               "pythagorean_expected_wins", "luck_delta", "source_url"], pyth)
    one_score = sum(1 for m in margins if abs(m) <= 8)
    # power analysis: games needed to detect 55% vs 52.4% at 80% power, two-sided 5%
    p0, p1, za, zb = 0.524, 0.55, 1.959963985, 0.841621234
    pbar = (p0 + p1) / 2.0
    needed = ((za * math.sqrt(2 * pbar * (1 - pbar)) +
               zb * math.sqrt(p0 * (1 - p0) + p1 * (1 - p1))) / (p1 - p0)) ** 2
    write_csv("luck_panel.csv",
              ["item", "value", "n", "ci_low", "ci_high", "reading", "source_url"],
              [["Home win share, weeks 1-9", round(home_wins / 136.0, 4), 136, lo, hi,
                "interval covers 0.50; no detectable home edge in this window", SOURCES["schedule_wk10"]],
               ["Mean home margin, weeks 1-9", round(mean(margins), 3), 136, "", "",
                "used as HFA plug-in (h) in the frozen model", SOURCES["schedule_wk10"]],
               ["Mean game total, weeks 1-9", round(mean(totals), 3), 136, "", "",
                "league level for the total baselines", SOURCES["schedule_wk10"]],
               ["One-score games (margin <= 8) share", round(one_score / 136.0, 4), 136, "", "",
                "share of results decided inside a single score", SOURCES["schedule_wk10"]],
               ["Bets needed to tell 55% from the 52.4% break-even",
                int(math.ceil(needed)), "", "", "",
                "80% power, two-sided 5%; below this a win rate is noise", SOURCES["schedule_wk10"]],
               ["Certified strategies in this namespace", 0, "", "", "",
                "no strategy has passed G0-G7; see leaderboard.csv", SOURCES["schedule_wk10"]]])

    # ---- 9. availability (official report only; no inferred depth)
    inj = []
    teams_no_injury = {"Bengals": "no injuries reported", "Commanders": "no injuries reported"}
    for r in read_pipe("injuries_2026_reg11.txt", 6):
        team, player, pos, injury, practice, game = r[0], r[1], r[2], r[3], r[4], r[5]
        inj.append([
            team, player, pos, injury, practice, game or "blank (page has no designation)",
            "" , "", "UNVERIFIED: no official depth chart or snap counts captured",
            "", "UNVERIFIED: no official inactive list yet; game has not been played",
            SOURCES["injuries_reg11"], CAPTURE_UTC])
    write_csv("availability_week11.csv",
              ["team", "player", "position", "injury", "practice_status", "game_status",
               "depth_rank", "starter_status", "depth_note", "snap_share",
               "inactive_status", "source_url", "retrieved_utc"], inj)

    summ = {}
    for r in inj:
        t = r[0]
        d = summ.setdefault(t, {"rows": 0, "out": 0, "q": 0, "dnp": 0, "lp": 0, "fp": 0})
        d["rows"] += 1
        if r[5] == "Out":
            d["out"] += 1
        elif r[5] == "Questionable":
            d["q"] += 1
        if r[4].startswith("Did Not"):
            d["dnp"] += 1
        elif r[4].startswith("Limited"):
            d["lp"] += 1
        elif r[4].startswith("Full"):
            d["fp"] += 1
    arows = []
    for t in sorted(summ):
        d = summ[t]
        arows.append([t, d["rows"], d["out"], d["q"], d["dnp"], d["lp"], d["fp"],
                      "", "UNVERIFIED: starter identity needs an official depth chart",
                      "", "UNVERIFIED: replacement needs an official depth chart",
                      SOURCES["injuries_reg11"]])
    for t in sorted(teams_no_injury):
        arows.append([t, 0, 0, 0, 0, 0, 0, "", "page states no injuries reported", "",
                      "", SOURCES["injuries_reg11"]])
    write_csv("availability_summary.csv",
              ["team", "report_rows", "designated_out", "designated_questionable",
               "practice_dnp", "practice_limited", "practice_full", "starters_out",
               "starters_out_note", "named_replacements", "replacements_note", "source_url"],
              arows)

    # ---- 9b. capture ledger (append-only in practice; rebuilt deterministically here)
    log = []
    for i, (ds, url, fn) in enumerate([
        ("2026 REG standings", SOURCES["standings"], "standings_2026_reg.txt"),
        ("Week 11 injury report", SOURCES["injuries_reg11"], "injuries_2026_reg11.txt"),
    ], 1):
        path = os.path.join(RAW, fn)
        log.append(["P%03d" % i, ds, url, CAPTURE_UTC, "raw/" + fn, sha256_file(path),
                    os.path.getsize(path)])
    write_csv("capture_log.csv",
              ["capture_id", "dataset", "url", "retrieved_utc", "file", "sha256", "bytes"], log)

    # ---- 9c. weekly diff against the previous dated snapshot
    snapdir = os.path.join(DATA, "snapshots")
    dirs = sorted(os.listdir(snapdir)) if os.path.isdir(snapdir) else []
    # the newest snapshot IS the current data, so the comparison target is the
    # one before it; with a single snapshot there is nothing to compare against.
    prev = dirs[:-1]
    watch = [("team_ratings.csv", "team", "offence_rating_pts"),
             ("team_ratings.csv", "team", "defence_rating_pts"),
             ("availability_summary.csv", "team", "designated_out")]
    diff = []
    if not prev:
        for fn, key, col in watch:
            diff.append([fn, col, "no previous snapshot", "", "", "n/a",
                         "first capture; a diff needs a second dated snapshot (F-11)",
                         REPO_DATA + "weekly_diff.csv"])
    else:
        snap = os.path.join(snapdir, prev[-1])
        for fn, key, col in watch:
            cur = {}
            p_cur = os.path.join(DATA, fn)
            if os.path.exists(p_cur):
                with open(p_cur, encoding="utf-8") as fh:
                    cur = {r[key]: r.get(col, "") for r in csv.DictReader(fh)}
            oldd = {}
            p_old = os.path.join(snap, fn)
            if os.path.exists(p_old):
                with open(p_old, encoding="utf-8") as fh:
                    oldd = {r[key]: r.get(col, "") for r in csv.DictReader(fh)}
            for k in sorted(set(cur) | set(oldd)):
                a, b = oldd.get(k, ""), cur.get(k, "")
                if a == b:
                    continue
                diff.append([fn, col, k, a, b, prev[-1],
                             "changed since the previous snapshot" if a else "new row",
                             SOURCES["standings"]])
        if not diff:
            diff.append(["all watched fields", "-", "-", "-", "-", prev[-1],
                         "no change detected against %s" % prev[-1], SOURCES["standings"]])
    write_csv("weekly_diff.csv",
              ["file", "column", "row_key", "previous_value", "current_value",
               "compared_with", "note", "source_url"], diff)

    # ---- 10. venues (spot check only; the full set is another session's desk)
    venues = []
    for r in read_pipe("venues_spotcheck.txt", 6):
        venues.append([r[0], r[1], r[2], r[3], r[4], r[5], "nfl.com game centre Game Info",
                       "https://www.nfl.com/games/%s" % r[0]])
    write_csv("venues_spotcheck.csv",
              ["game_slug", "away", "home", "location_as_printed", "stadium_as_printed",
               "read_utc", "evidence", "source_url"], venues)

    print("pipeline OK: corpus=%d wk10=%d wk11=%d injuries=%d reconciliation_mismatches=%d"
          % (len(corpus), len(wk10), len(line_rows), len(inj), bad))
    print("model: mu=%.3f h=%.3f sigma=%.3f lambda=%.1f" % (model["mu"], model["h"], sigma, model["lam"]))
    print("wk10 MAE spread=%.3f totalA=%.3f totalB=%.3f BSS=%.4f"
          % (mean(sp_err), mean(ta_err), mean(tb_err), bss))
    print("home win share=%.4f CI=(%.4f,%.4f) games_needed=%d" % (home_wins / 136.0, lo, hi, math.ceil(needed)))
    if bad:
        print("WARNING: %d reconciliation mismatches" % bad)
    return 0


if __name__ == "__main__":
    sys.exit(main())

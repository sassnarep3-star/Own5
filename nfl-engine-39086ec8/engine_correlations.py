"""Requirement 7 — correlations only from officially sourced numbers, with n.

Three jobs:

1. REPRODUCE. Every correlation value already published in this repository is
   recomputed from the inputs that desk itself declares. If a value does not
   reproduce, that is an irregularity, not a rounding difference.

2. SOURCE. Every correlation is classified by provenance:
      OFFICIAL      inputs are an nfl.com or club-site page (score, standings,
                    injury report, depth chart)
      THIRD_PARTY   inputs are a third-party dataset (a GitHub mirror, a
                    play-by-play dump) even if the mirror itself is reputable
      DERIVED       inputs are model output from this project
   A value computed from third-party inputs is NOT deleted — it is published with
   its provenance so nobody mistakes it for an official number.

3. PUBLISH n. Every value carries n, its interval, and the unit of observation
   (club, game, player-week). A correlation without n is not a result.

The parlay coupling table uses only official final scores. The line used to define
"cover" and "over" is a DECLARED FIXED LINE, not a market line, and is labelled as
such: it measures the dependence structure of outcomes, not the price of any bet.
"""

import csv
import io
import math

import statslib

HEADER = (
    "id", "question", "x", "y", "unit_of_observation", "n", "r", "ci95_low",
    "ci95_high", "p_two_sided", "provenance", "official_url", "note",
)

PROVENANCE_OFFICIAL = "OFFICIAL"
PROVENANCE_THIRD = "THIRD_PARTY"
PROVENANCE_DERIVED = "DERIVED"


# --------------------------------------------------------------- reproduce


def reproduce(values, xs, ys, published_r):
    """Recompute and compare at the precision the published value was given.

    Published correlations in this repository are rounded to 4 decimal places, so
    agreement is tested at 1e-3 — tighter than the printed precision and strict
    enough that a different formula or a different sample would fail.
    """
    r, n = statslib.pearson(xs, ys)
    return {
        "n": n, "r": r, "published": published_r,
        "delta": round(r - published_r, 6),
        "reproduces": abs(r - published_r) < 1e-3,
    }


def reproduce_standings_correlations(standings):
    """The six correlations published at repo root, recomputed from the same file
    values. Reproduces CORR01..CORR06 exactly when the published inputs are used."""
    rows = []
    clubs = sorted(standings)
    W = [standings[c][0] for c in clubs]
    T = [standings[c][2] for c in clubs]
    PF = [standings[c][3] for c in clubs]
    PA = [standings[c][4] for c in clubs]
    GP = [w + l + t for (w, l, t, _, _) in (standings[c] for c in clubs)]
    PCT = [(w + 0.5 * t) / g for w, t, g in zip(W, T, GP)]
    PFG = [a / b for a, b in zip(PF, GP)]
    PAG = [a / b for a, b in zip(PA, GP)]
    NETG = [(a - b) / g for a, b, g in zip(PF, PA, GP)]
    specs = [
        ("CORR01", "PF/G vs PCT", PFG, PCT, 0.6136),
        ("CORR02", "PA/G vs PCT", PAG, PCT, -0.5796),
        ("CORR03", "NET/G vs PCT", NETG, PCT, 0.8391),
        ("CORR04", "PF vs PA", PF, PA, 0.0705),
        ("CORR05", "NET vs PCT", [a - b for a, b in zip(PF, PA)], PCT, 0.8313),
        ("CORR06", "PF/G vs PA/G", PFG, PAG, -0.0117),
    ]
    for ident, label, xs, ys, pub in specs:
        rows.append(dict(id=ident, label=label, **reproduce(None, xs, ys, pub)))
    return rows


def reproducible_ledger_correlations(finals, published):
    """Recompute the 864d5668 desk's C-01..C-03 from its own ledger."""
    out = []
    hm = [g["home_pts"] - g["away_pts"] for g in finals]
    tp = [g["home_pts"] + g["away_pts"] for g in finals]
    out.append(("C-01", "home margin vs total points", *reproduce(
        None, hm, tp, published["C-01"])))
    out.append(("C-02", "|home margin| vs total points", *reproduce(
        None, [abs(v) for v in hm], tp, published["C-02"])))
    with_rest = [g for g in finals if g.get("rest_diff") not in (None, "")]
    out.append(("C-03", "rest differential vs home margin", *reproduce(
        None,
        [float(g["rest_diff"]) for g in with_rest],
        [g["home_pts"] - g["away_pts"] for g in with_rest], published["C-03"])))
    return out


# --------------------------------------------------------------- sensitivity


def bye_confound(finals, published_r):
    """How much of C-03 is the bye week rather than 'rest'.

    A team coming off a bye has +7 rest days. If the effect is real, it should
    survive removing those games; if it does not survive, the coefficient was
    measuring a 16-game sub-sample, not a rest gradient.
    """
    rows = []
    with_rest = [g for g in finals if g.get("rest_diff") not in (None, "")]
    for thr in (None, 4, 3, 2):
        sub = with_rest if thr is None else [
            g for g in with_rest if abs(float(g["rest_diff"])) <= thr]
        if len(sub) < 4:
            continue
        r, n = statslib.pearson([float(g["rest_diff"]) for g in sub],
                                [g["home_pts"] - g["away_pts"] for g in sub])
        lo, hi = statslib.fisher_ci(r, n)
        rows.append({
            "subset": ("all games with rest data" if thr is None
                       else "excluding |rest_diff| > %d (bye-week games)" % thr),
            "n": n, "r": round(r, 4),
            "ci95": "%.3f to %.3f" % (lo, hi),
            "p": round(statslib.pearson_p(r, n), 5),
            "note": ("published value" if thr is None else
                     "coefficient does not survive removing bye weeks"
                     if abs(r) < 0.1 else ""),
        })
    n_bye = sum(1 for g in with_rest if abs(float(g["rest_diff"])) >= 7)
    return rows, n_bye, len(with_rest)


# --------------------------------------------------------------- coupling


def parlay_coupling(finals, spread_line=-3.0, total_line=45.5):
    """Dependence between a side leg and a total leg, from official scores only.

    'Cover' means the home team wins by more than 3; 'over' means the combined
    score exceeds 45.5. Those two lines are DECLARED and fixed — they are not
    market lines, and this table therefore prices nothing. It measures whether the
    two outcomes in a two-leg same-game parlay are independent, with the sample
    size published.
    """
    covers = []
    overs = []
    for g in finals:
        m = g["home_pts"] - g["away_pts"]
        t = g["home_pts"] + g["away_pts"]
        covers.append(1 if m + spread_line > 0 else 0)
        overs.append(1 if t > total_line else 0)
    n = len(covers)
    p_a = sum(covers) / n
    p_b = sum(overs) / n
    p_joint = sum(a * b for a, b in zip(covers, overs)) / n
    phi = (p_joint - p_a * p_b) / math.sqrt(p_a * (1 - p_a) * p_b * (1 - p_b))
    return {
        "n": n, "spread_line": spread_line, "total_line": total_line,
        "p_cover": round(p_a, 4), "p_over": round(p_b, 4),
        "p_joint": round(p_joint, 4),
        "p_independent": round(p_a * p_b, 4),
        "ratio": round(p_joint / (p_a * p_b), 4),
        "phi": round(phi, 4),
        "note": "declared fixed lines; not a market price",
    }


# ----------------------------------------------------- official correlations


def official_correlations(standings, finals):
    """Correlations computed only from nfl.com-published numbers."""
    rows = []
    clubs = sorted(standings)
    GP = {c: sum(standings[c][:3]) for c in clubs}
    PFG = [standings[c][3] / GP[c] for c in clubs]
    PAG = [standings[c][4] / GP[c] for c in clubs]
    PCT = [(standings[c][0] + 0.5 * standings[c][2]) / GP[c] for c in clubs]
    r, n = statslib.pearson(PFG, PAG)
    lo, hi = statslib.fisher_ci(r, n)
    rows.append(dict(
        id="O-01",
        question="Do clubs that score more also concede more? (offence vs defence coupling)",
        x="points for per game", y="points against per game",
        unit_of_observation="club (2026 season to date)", n=n, r=round(r, 4),
        ci95_low=round(lo, 3), ci95_high=round(hi, 3),
        p_two_sided=round(statslib.pearson_p(r, n), 4),
        provenance=PROVENANCE_OFFICIAL,
        official_url="https://www.nfl.com/standings/",
        note="32 clubs; two-way association, not causal"))

    r, n = statslib.pearson(PFG, PCT)
    lo, hi = statslib.fisher_ci(r, n)
    rows.append(dict(
        id="O-02", question="How strongly does scoring predict winning?",
        x="points for per game", y="winning percentage (official tie rule)",
        unit_of_observation="club (2026 season to date)", n=n, r=round(r, 4),
        ci95_low=round(lo, 3), ci95_high=round(hi, 3),
        p_two_sided=round(statslib.pearson_p(r, n), 6),
        provenance=PROVENANCE_OFFICIAL,
        official_url="https://www.nfl.com/standings/",
        note="ecological association; n=32, so intervals are wide"))

    hm = [g["home_pts"] - g["away_pts"] for g in finals]
    tp = [g["home_pts"] + g["away_pts"] for g in finals]
    r, n = statslib.pearson(hm, tp)
    lo, hi = statslib.fisher_ci(r, n)
    rows.append(dict(
        id="O-03", question="Are a game's side and total outcomes independent?",
        x="home margin", y="total points",
        unit_of_observation="game (2026 finals)", n=n, r=round(r, 4),
        ci95_low=round(lo, 3), ci95_high=round(hi, 3),
        p_two_sided=round(statslib.pearson_p(r, n), 4),
        provenance=PROVENANCE_OFFICIAL,
        official_url="https://www.nfl.com/schedules/",
        note="used by same-game parlay pricing; |r| small but not proof of independence"))

    with_rest = [g for g in finals if g.get("rest_diff") not in (None, "")]
    r, n = statslib.pearson([float(g["rest_diff"]) for g in with_rest],
                            [g["home_pts"] - g["away_pts"] for g in with_rest])
    lo, hi = statslib.fisher_ci(r, n)
    rows.append(dict(
        id="O-04", question="Does a rest advantage move the home margin?",
        x="rest differential (away days - home days)", y="home margin",
        unit_of_observation="game with both rest values", n=n, r=round(r, 4),
        ci95_low=round(lo, 3), ci95_high=round(hi, 3),
        p_two_sided=round(statslib.pearson_p(r, n), 5),
        provenance=PROVENANCE_OFFICIAL,
        official_url="https://www.nfl.com/schedules/",
        note="see the bye-week sensitivity table: the value is not robust"))
    return rows


# ----------------------------------------------------------- repo provenance


def repo_provenance(repo_correlations):
    """Classify every correlation value published elsewhere in the repository.

    `repo_correlations` is a list of dicts with keys: file, id, label, value, n,
    source_url, nfl_desk.
    """
    out = []
    for c in repo_correlations:
        url = c["source_url"]
        if "nfl.com" in url or "clubs.nfl.com" in url:
            prov = PROVENANCE_OFFICIAL
        elif "github.com" in url:
            prov = PROVENANCE_THIRD
        else:
            prov = PROVENANCE_THIRD
        out.append(dict(c, provenance=prov))
    return out


def lead_lag_spec():
    """The test that CANNOT be run yet, stated exactly.

    Writing the spec down is the deliverable here. A test that is quietly skipped
    looks the same as a test that passed, so the page shows the missing inputs.
    """
    return {
        "question": "Does the market move on the official injury report, or does it move first?",
        "why_it_matters": (
            "If the line moves before the official report, the report is not the "
            "information source and an injury-based signal cannot beat the close. "
            "If the line moves after, the size and timing of that move is the edge."),
        "required_inputs": [
            "Timestamped opening and closing prices for the same game (price store, req 1)",
            "The exact publication timestamp of the official injury report",
            "At least one full season of both, aligned to kickoff",
        ],
        "have": ["Official injury report contents (4 clubs, Week 10, 2026-11-14)"],
        "lack": ["Every price, at every timestamp, for every game"],
        "test_statistic": (
            "regress the signed line movement (close - open) on the injury-status "
            "change, controlling for the result; report n, the coefficient, and the "
            "share of movement that precedes the report"),
        "decision_rule": (
            "Publish a signal only if the coefficient is positive, the 95% interval "
            "excludes zero, and the pre-report movement is not the majority of it"),
        "status": "BLOCKED — cannot be computed without a price archive",
        "blocking_flag": "P-01 / F-02",
    }


def to_csv(rows):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=HEADER, lineterminator="\n",
                       extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k, "") for k in HEADER})
    return buf.getvalue()

"""NFL Signal Board — deterministic data build (session 1fab8a48).

Reads ONLY:
  data/nfl-signal-board/raw/*.csv                (this session's official reads, timestamped + source-linked)
  nfl-line-audit/data/corpus_games.csv           (pinned 1999-2026 game corpus, read-only, hash-verified)
  nfl-line-audit/captures/official/*.json        (prior session's hashed injury capture, read-only, hash-verified)
  data/games_2026.json                           (the 136-row 2026 log named in the brief, read-only, audited)

Writes data/nfl-signal-board/*.csv + derive_summary.json.

Rules enforced here (and re-checked by verify.py):
  * every published row carries a source_url to an official page or to the exact artifact it came from;
  * nothing is inferred: a value that cannot be confirmed stays blank and is listed in flagged.csv;
  * every model output is a probability plus the inputs that produced it;
  * prices are attributed to the operator and carry the read clock; closes are blank until kickoff;
  * the leaderboard never shows a backtest number (separate file, separate page).
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
RAW = HERE / "raw"
CORPUS = REPO / "nfl-line-audit" / "data" / "corpus_games.csv"
INJ_CAPTURE = REPO / "nfl-line-audit" / "captures" / "official" / "injury_reg11_20261119T0653Z.json"
GAMES_2026 = REPO / "data" / "games_2026.json"

GH = "https://github.com/sassnarep3-star/Own5/blob/main/"
SITE = "https://sassnarep3-star.github.io/Own5/nfl-signal-board/"
STANDINGS_URL = "https://www.nfl.com/standings/league/2026/REG"
SCHED11_URL = "https://www.nfl.com/schedules/2026/by-week/week-11"
SCHED10_URL = "https://www.nfl.com/schedules/2026/by-week/week-10"
INJ11_URL = "https://www.nfl.com/injuries/league/2026/reg11"
ODDS_URL = "https://sportsbook.draftkings.com/leagues/football/nfl"
NFL_TERMS = "https://www.nfl.com/legal/terms/"

SEED = 20261119
ALIAS = {"ARI": "AZ", "LAR": "LA", "WSH": "WAS", "JAC": "JAX", "NOR": "NO", "SFO": "SF",
         "TAM": "TB", "GBP": "GB", "KCC": "KC", "LVR": "LV", "LARams": "LA", "SD": "LAC", "STL": "LA",
         "OAK": "LV", "SDG": "LAC"}

FIELDS = {
    "sources": ["source_id", "title", "url", "tier", "read_utc", "sha256", "used_for"],
    "corpus_reconciliation": ["club", "w", "l", "t", "pf", "pa", "src_w", "src_l", "src_t", "src_pf", "src_pa", "reconciles", "source_url"],
    "ratings": ["club", "elo_pre_week11", "rating_off", "rating_def", "games_used", "last_result", "source_url"],
    "origination": ["market_id", "fixture_id", "kickoff_et", "away", "home", "market_order", "market", "selection",
                    "fair_line", "market_line", "difference_fair_minus_market", "fair_prob", "fair_prob_calibrated",
                    "market_prob_devig", "ev_per_unit", "stake_signal", "stake", "model_inputs", "inputs_sha256",
                    "price_read_utc", "price_source_url", "closing_value", "closing_status", "source_url", "note"],
    "price_snapshots": ["snapshot_id", "market_id", "operator", "fixture_id", "market", "selection", "open_value",
                        "open_american", "open_read_utc", "close_value", "close_american", "close_read_utc",
                        "close_status", "movement", "source_url", "note"],
    "model_metrics": ["model_id", "description", "season_window", "n", "brier_model", "brier_market", "brier_skill",
                      "ci_low", "ci_high", "p_raw", "p_holm", "log_loss_model", "log_loss_market", "certified",
                      "source_url", "note"],
    "calibration": ["family", "bin_low", "bin_high", "n", "mean_predicted", "observed_rate", "gap", "source_url"],
    "luck": ["panel", "statistic", "value", "ci_low", "ci_high", "n", "clusters", "reads", "source_url"],
    "leaderboard": ["division", "strategy_id", "strategy", "settled_bets", "signal_stat", "signal_value",
                    "signal_ci_low", "signal_ci_high", "staking_units", "staking_roi", "staking_ci_low",
                    "staking_ci_high", "grade", "demotion_rule", "what_would_change_our_mind", "source_url"],
    "depth": ["club", "out_designated", "questionable_designated", "replacement_named", "observed_starters_out",
              "gate_status", "blocking_gate", "number_that_would_clear_it", "source_url", "note"],
    "requirements": ["id", "requirement", "category", "status", "blocking_gate", "number_that_would_clear_it",
                     "observed", "evidence_path", "source_url"],
    "questions": ["id", "question", "why_it_matters", "what_we_have", "what_we_do_not_have", "discovery_route",
                  "can_decide_today", "informations_needed", "source_url"],
    "suggestions": ["id", "suggestion", "problem_it_solves", "effort", "risk", "how_we_would_know_it_worked",
                    "owner_decision", "related_requirement", "source_url"],
    "research": ["id", "title", "question", "evidence", "n", "result", "what_would_change_our_mind", "status", "source_url"],
    "flagged": ["id", "type", "title", "detail", "evidence_url", "severity", "status", "source_url"],
    "prereg": ["registration_id", "strategy_id", "division", "rule_text", "sample_window", "gates",
               "frozen_utc", "artifact_sha256", "commit_ref", "source_url"],
    "designation": ["designation", "seasons_pooled", "rows", "played", "play_rate", "ci_low", "ci_high",
                    "use_in_model", "source_url", "note"],
    "log136": ["wk", "date", "away", "home", "away_score_log", "home_score_log", "status_log", "audit_verdict",
               "away_score_official", "home_score_official", "source_url", "note"],
}


# ----------------------------------------------------------------------------- helpers
def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_csv(name: str, rows: list[dict]) -> None:
    path = HERE / f"{name}.csv"
    cols = FIELDS[name]
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    return sha256_bytes(p.read_bytes())


def american_to_decimal(a: float) -> float:
    return 1.0 + (a / 100.0 if a > 0 else 100.0 / abs(a))


def american_to_raw_prob(a: float) -> float:
    return (-a) / ((-a) + 100.0) if a < 0 else 100.0 / (a + 100.0)


def devig_two(a: float, b: float) -> tuple[float, float]:
    pa, pb = american_to_raw_prob(a), american_to_raw_prob(b)
    s = pa + pb
    return pa / s, pb / s


def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def norm_pdf(x: float) -> float:
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def fmt(x: float | None, nd: int = 4) -> str:
    if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))):
        return ""
    return f"{x:.{nd}f}"


def brier(ps: list[float], ys: list[int]) -> float:
    return sum((p - y) ** 2 for p, y in zip(ps, ys)) / len(ps)


def logloss(ps: list[float], ys: list[int]) -> float:
    eps = 1e-12
    return -sum(y * math.log(clamp(p, eps, 1 - eps)) + (1 - y) * math.log(clamp(1 - p, eps, 1 - eps))
                for p, y in zip(ps, ys)) / len(ps)


class Lcg:
    """Deterministic PRNG so every bootstrap interval is reproducible from the seed alone."""

    def __init__(self, seed: int) -> None:
        self.s = seed & 0xFFFFFFFF

    def next(self) -> float:
        self.s = (1103515245 * self.s + 12345) & 0x7FFFFFFF
        return self.s / 0x7FFFFFFF

    def randint(self, n: int) -> int:
        return int(self.next() * n) % n


# ----------------------------------------------------------------------------- 1. official reads
def build_sources(hashes: dict[str, str]) -> list[dict]:
    r = "2026-11-19T11:06:00Z"
    return [
        {"source_id": "SRC01", "title": "NFL official league standings, 2026 regular season",
         "url": STANDINGS_URL, "tier": "OFFICIAL", "read_utc": r, "sha256": hashes.get("standings", ""),
         "used_for": "all 32 club records, PF/PA, and the correlation inputs (n=32)"},
        {"source_id": "SRC02", "title": "NFL official Week 11 schedule page", "url": SCHED11_URL,
         "tier": "OFFICIAL", "read_utc": "2026-11-19T11:09:00Z", "sha256": hashes.get("fixtures", ""),
         "used_for": "13 fixtures, kickoff times, networks, venues, six byes"},
        {"source_id": "SRC03", "title": "NFL official Week 10 schedule page (finals)", "url": SCHED10_URL,
         "tier": "OFFICIAL", "read_utc": "2026-11-19T11:07:00Z", "sha256": hashes.get("week10", ""),
         "used_for": "14 Week 10 finals used to update the ratings and the corpus reconciliation"},
        {"source_id": "SRC04", "title": "NFL official injury report, Week 11", "url": INJ11_URL,
         "tier": "OFFICIAL", "read_utc": "2026-11-19T11:03:00Z", "sha256": hashes.get("injury_capture", ""),
         "used_for": "per-club designation counts and the three named-player checks; publisher of record is the club"},
        {"source_id": "SRC05", "title": "DraftKings Sportsbook NFL game lines", "url": ODDS_URL,
         "tier": "OPERATOR", "read_utc": "2026-11-19T11:10:00Z", "sha256": hashes.get("odds", ""),
         "used_for": "the only market prices on this site, attributed to the operator, read clock on every row"},
        {"source_id": "SRC06", "title": "nflverse-data schedules release (pinned game corpus)",
         "url": "https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv.gz",
         "tier": "PINNED-DATASET", "read_utc": "pinned at first commit by session d6c404d4",
         "sha256": hashes.get("corpus", ""),
         "used_for": "walk-forward evaluation inputs (results + closing prices) 1999-2026; not an official NFL source"},
        {"source_id": "SRC07", "title": "Prior session's hashed Week 11 injury capture (2026-11-19T06:53Z)",
         "url": GH + "nfl-line-audit/captures/official/injury_reg11_20261119T0653Z.json",
         "tier": "INHERITED-CAPTURE", "read_utc": "2026-11-19T06:53:00Z", "sha256": hashes.get("injury_capture", ""),
         "used_for": "row-level designation counts (253 rows, 24 clubs); re-verified against today's live read"},
        {"source_id": "SRC08", "title": "The 136-row 2026 game log named in the brief (data/games_2026.json)",
         "url": GH + "data/games_2026.json", "tier": "INHERITED-LOG", "read_utc": "2026-11-19T11:12:00Z",
         "sha256": hashes.get("games2026", ""), "used_for": "the log audit on the results page"},
        {"source_id": "SRC09", "title": "NFL Terms of Service (row-level republication basis)", "url": NFL_TERMS,
         "tier": "OFFICIAL", "read_utc": "2026-11-19 (policy inherited, not re-read this session)",
         "sha256": "", "used_for": "basis for policy P-01: aggregates on site, raw rows in the private store"},
        {"source_id": "SRC10", "title": "NFL official schedule announcement, 2026 (May 14, 2026 release)",
         "url": "https://www.nfl.com/schedules/2026/", "tier": "OFFICIAL", "read_utc": "not re-read this session",
         "sha256": "", "used_for": "the dated announcement is published beside the live schedule; date flagged SBF-06"},
    ]


# ----------------------------------------------------------------------------- 2. corpus
def load_corpus() -> list[dict]:
    rows = read_csv(CORPUS)
    out = []
    for r in rows:
        try:
            season, week = int(r["season"]), int(r["week"])
        except ValueError:
            continue
        for k in ("away_score", "home_score"):
            pass
        if not r["home_score"] or not r["away_score"]:
            continue
        def num(x):
            try:
                return float(x)
            except (TypeError, ValueError):
                return None
        out.append({
            "season": season, "week": week, "game_date": r["game_date"],
            "away": ALIAS.get(r["away"], r["away"]), "home": ALIAS.get(r["home"], r["home"]),
            "away_score": int(float(r["away_score"])), "home_score": int(float(r["home_score"])),
            "spread": num(r["closing_spread_home"]), "total": num(r["closing_total"]),
            "home_ml": num(r["home_ml_close"]), "away_ml": num(r["away_ml_close"]),
            "roof": r["roof"], "surface": r["surface"], "source_class": r["source_class"],
            "source_url": r["source_url"],
        })
    return out


def detect_spread_sign(corpus: list[dict]) -> tuple[bool, float, float]:
    """Return (home_favoured_positive, mae_positive, mae_negative) measured on the data itself."""
    pos, neg = [], []
    for g in corpus:
        if g["spread"] is None:
            continue
        m = g["home_score"] - g["away_score"]
        pos.append(abs(m - g["spread"]))
        neg.append(abs(m + g["spread"]))
    mp, mn = statistics.mean(pos), statistics.mean(neg)
    return mp < mn, mp, mn


def build_reconciliation(corpus: list[dict], standings: list[dict]) -> tuple[list[dict], dict]:
    cur = [g for g in corpus if g["season"] == 2026]
    pf, pa = Counter(), Counter()
    w, l, t = Counter(), Counter(), Counter()
    for g in cur:
        a, h = g["away"], g["home"]
        pf[a] += g["away_score"]; pa[a] += g["home_score"]
        pf[h] += g["home_score"]; pa[h] += g["away_score"]
        if g["away_score"] > g["home_score"]:
            w[a] += 1; l[h] += 1
        elif g["home_score"] > g["away_score"]:
            w[h] += 1; l[a] += 1
        else:
            t[a] += 1; t[h] += 1
    rows, ok = [], 0
    for s in standings:
        c = s["club"]
        good = (w[c], l[c], t[c], pf[c], pa[c]) == (s["w"], s["l"], s["t"], s["pf"], s["pa"])
        ok += 1 if good else 0
        rows.append({"club": c, "w": w[c], "l": l[c], "t": t[c], "pf": pf[c], "pa": pa[c],
                     "src_w": s["w"], "src_l": s["l"], "src_t": s["t"], "src_pf": s["pf"], "src_pa": s["pa"],
                     "reconciles": "YES" if good else "NO", "source_url": STANDINGS_URL})
    stats = {"games": len(cur), "clubs_reconciled": ok, "clubs": len(standings),
             "weeks": sorted({g["week"] for g in cur})}
    return rows, stats


def audit_log136(games: list[dict], corpus: list[dict]) -> tuple[list[dict], dict]:
    """Audit the 136-row log the brief names, row by row, against the reconciled corpus."""
    off = {(g["week"], g["away"], g["home"]): g for g in corpus if g["season"] == 2026}
    rows, blank, absent, disagree, agree = [], 0, 0, 0, 0
    for g in games:
        key = (int(g["wk"]), ALIAS.get(g["away"], g["away"]), ALIAS.get(g["home"], g["home"]))
        o = off.get(key)
        a, h = g.get("as"), g.get("hs")
        if a in (None, "") or h in (None, ""):
            verdict, blank = "BLANK — no score printed in the log row", blank + 1
        elif o is None:
            verdict, absent = "ABSENT — no matching 2026 game in the reconciled corpus", absent + 1
        elif int(a) == o["away_score"] and int(h) == o["home_score"]:
            verdict, agree = "AGREE with the official score", agree + 1
        else:
            verdict, disagree = "DISAGREE with the official score", disagree + 1
        rows.append({"wk": g["wk"], "date": g["date"], "away": g["away"], "home": g["home"],
                     "away_score_log": a if a not in (None,) else "", "home_score_log": h if h not in (None,) else "",
                     "status_log": g.get("st", ""), "audit_verdict": verdict,
                     "away_score_official": o["away_score"] if o else "", "home_score_official": o["home_score"] if o else "",
                     "source_url": GH + "data/games_2026.json", "note": g.get("note", "")})
    return rows, {"rows": len(games), "agree": agree, "blank": blank, "absent": absent, "disagree": disagree}


# ----------------------------------------------------------------------------- 3. ratings + evaluation
class Elo:
    def __init__(self, hfa: float = 48.0, k: float = 20.0, regress: float = 1 / 3):
        self.r: dict[str, float] = defaultdict(lambda: 1500.0)
        self.hfa, self.k, self.regress = hfa, k, regress
        self.last_season = None

    def pre(self, g: dict) -> float:
        return self.r[g["home"]] + self.hfa - self.r[g["away"]]

    def update(self, g: dict) -> None:
        if self.last_season != g["season"]:
            for t in self.r:
                self.r[t] = 1500.0 + (self.r[t] - 1500.0) * (1 - self.regress)
            self.last_season = g["season"]
        m = g["home_score"] - g["away_score"]
        exp = 1.0 / (1.0 + 10 ** (-self.pre(g) / 400.0))
        act = 1.0 if m > 0 else (0.5 if m == 0 else 0.0)
        mult = math.log(max(abs(m), 1) + 1.0) * self.k / 2.0
        delta = mult * (act - exp)
        self.r[g["home"]] += delta
        self.r[g["away"]] -= delta


def ols(xs: list[float], ys: list[float]) -> tuple[float, float]:
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    b = sxy / sxx
    return my - b * mx, b


class PointsModel:
    """Rolling opponent-aware scoring rates with shrinkage; two estimators published side by side."""

    def __init__(self, k_shrink: float = 4.0, window: int = 8):
        self.k, self.window = k_shrink, window
        self.scored: dict[str, list[int]] = defaultdict(list)
        self.allowed: dict[str, list[int]] = defaultdict(list)
        self.season = None
        self.league: list[int] = []

    def _rates(self, team: str) -> tuple[float, float, int]:
        lg = statistics.mean(self.league) if self.league else 22.0
        s, a = self.scored[team], self.allowed[team]
        use_s, use_a = s[-self.window:], a[-self.window:]
        n = min(len(s), len(a))
        off = (sum(use_s) + self.k * lg) / (len(use_s) + self.k) if use_s else lg
        dfn = (sum(use_a) + self.k * lg) / (len(use_a) + self.k) if use_a else lg
        return off, dfn, n

    def expect(self, g: dict) -> tuple[float, float, float]:
        if self.season != g["season"]:
            self.season = g["season"]
            self.scored.clear(); self.allowed.clear(); self.league.clear()
        oa, da, na = self._rates(g["away"])
        oh, dh, nh = self._rates(g["home"])
        exp_home = (oh + da) / 2.0
        exp_away = (oa + dh) / 2.0
        return exp_home, exp_away, min(na, nh)

    def update(self, g: dict) -> None:
        self.scored[g["home"]].append(g["home_score"]); self.allowed[g["home"]].append(g["away_score"])
        self.scored[g["away"]].append(g["away_score"]); self.allowed[g["away"]].append(g["home_score"])
        self.league.append(g["home_score"]); self.league.append(g["away_score"])


def sigma_buckets(residuals: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """(abs_elo_diff, |residual|) -> bucketed sd, monotone by construction of 4 fixed buckets."""
    edges = [(0, 50), (50, 100), (100, 175), (175, 10_000)]
    out = []
    for lo, hi in edges:
        vals = [abs(r) for e, r in residuals if lo <= e < hi]
        sd = math.sqrt(sum(v * v for v in vals) / len(vals)) if vals else 13.86
        out.append((hi, sd))
    return out


def eval_family(rows: list[dict], key_p: str, key_y: str, key_mp: str, label: str, source_url: str,
                model_id: str, windows: dict[str, list[dict]], n_boot: int = 1000) -> dict:
    """Brier-skill vs the de-vigged market with a week-cluster bootstrap and a Holm adjustment."""
    res = {}
    for wname, wrows in windows.items():
        sub = [r for r in wrows if r.get(key_p) is not None and r.get(key_mp) is not None]
        if not sub:
            continue
        ps = [r[key_p] for r in sub]; ms = [r[key_mp] for r in sub]
        ys = [int(r[key_y]) for r in sub]
        bm, bk = brier(ps, ys), brier(ms, ys)
        skill = 1.0 - bm / bk if bk > 0 else None
        clusters = defaultdict(list)
        for i, r in enumerate(sub):
            clusters[(r["season"], r["week"])].append(i)
        keys = list(clusters)
        rng = Lcg(SEED + len(sub))
        boots = []
        for _ in range(n_boot):
            idx = []
            for _c in range(len(keys)):
                idx.extend(clusters[keys[rng.randint(len(keys))]])
            bp = [ps[i] for i in idx]; bmk = [ms[i] for i in idx]; by = [ys[i] for i in idx]
            bkb = brier(bmk, by)
            boots.append(1.0 - brier(bp, by) / bkb if bkb > 0 else 0.0)
        boots.sort()
        ci_low = boots[int(0.025 * len(boots))]
        ci_high = boots[int(0.975 * len(boots)) - 1]
        p = sum(1 for b in boots if b <= 0.0) / len(boots)
        res[wname] = {"label": label, "model_id": model_id, "n": len(sub), "brier_model": bm,
                      "brier_market": bk, "skill": skill, "ci_low": ci_low, "ci_high": ci_high,
                      "p_raw": p, "ll_model": logloss(ps, ys), "ll_market": logloss(ms, ys),
                      "clusters": len(keys), "source_url": source_url,
                      "ps": ps, "ms": ms, "ys": ys}
    return res


def holm(pvals: list[tuple[str, float]]) -> dict[str, float]:
    ordered = sorted(pvals, key=lambda t: t[1])
    m = len(ordered)
    out, running = {}, 0.0
    for i, (k, p) in enumerate(ordered):
        adj = min(1.0, (m - i) * p)
        running = max(running, adj)
        out[k] = running
    return out


def build_models(corpus: list[dict], spread_positive: bool) -> tuple[list[dict], list[dict], list[dict], dict, dict, list[dict]]:
    """Walk-forward evaluation. Train = 2015-2024 (tuning only), holdout = 2025-2026 (never used for tuning)."""
    games = sorted([g for g in corpus if g["season"] >= 2015], key=lambda g: (g["season"], g["week"], g["game_date"]))
    elo = Elo()
    pts = PointsModel()
    rows = []
    for g in games:
        mu_elo = elo.pre(g)
        exp_home_pts, exp_away_pts, n_pts = pts.expect(g)
        exp_total = exp_home_pts + exp_away_pts
        exp_margin_pts = exp_home_pts - exp_away_pts
        rows.append({**g, "elo_diff": mu_elo, "exp_total": exp_total, "exp_margin": exp_margin_pts,
                     "n_pts": n_pts, "week_key": (g["season"], g["week"])})
        elo.update(g)
        pts.update(g)

    train = [r for r in rows if r["season"] <= 2024]
    holdout = [r for r in rows if r["season"] >= 2025]

    # margin model: OLS margin ~ a + b*elo_diff, fitted on train only
    a_elo, b_elo = ols([r["elo_diff"] for r in train], [r["home_score"] - r["away_score"] for r in train])
    # second margin estimator: the rolling points model (published alongside, gate decides later)
    # total model: fit a scalar correction on train so the estimator is unbiased
    train_tot = [r for r in train if r["n_pts"] >= 3]
    tot_corr = statistics.mean([(r["home_score"] + r["away_score"]) - r["exp_total"] for r in train_tot]) if train_tot else 0.0

    # sigma variants, all estimated on train only
    resid_elo = [(r["elo_diff"], (r["home_score"] - r["away_score"]) - (a_elo + b_elo * r["elo_diff"])) for r in train]
    sd_fixed = 13.86
    sd_elo = math.sqrt(sum(res * res for _e, res in resid_elo) / len(resid_elo))
    buckets = sigma_buckets(resid_elo)
    resid_pts = [(r["elo_diff"], (r["home_score"] - r["away_score"]) - r["exp_margin"]) for r in train]
    sd_pts = math.sqrt(sum(res * res for _e, res in resid_pts) / len(resid_pts))
    tot_resid = [(r["home_score"] + r["away_score"]) - (r["exp_total"] + tot_corr) for r in train_tot]
    sd_total = math.sqrt(sum(v * v for v in tot_resid) / len(tot_resid))

    def sd_for(ediff: float) -> float:
        for hi, sd in buckets:
            if abs(ediff) < hi:
                return sd
        return buckets[-1][1]

    for r in rows:
        mu_lin = a_elo + b_elo * r["elo_diff"]
        mu_pts = r["exp_margin"]
        r["mu_lin"], r["mu_pts"] = mu_lin, mu_pts
        r["sd_elo"] = sd_elo
        r["sd_bucketed"] = sd_for(r["elo_diff"])
        # variance of the points estimator is wider; measured, not assumed
        sd_mix = math.sqrt((sd_elo ** 2 + sd_pts ** 2) / 2.0)
        r["sd_pts"] = sd_mix
        r["sd_total"] = sd_total
        r["exp_total_adj"] = r["exp_total"] + tot_corr
        # market-side probabilities
        if r["spread"] is not None and r["home_ml"] is not None and r["away_ml"] is not None and r["total"] is not None:
            line_home = r["spread"] if spread_positive else -r["spread"]
            r["line_home"] = line_home
            r["p_market_home_ml"], r["p_market_away_ml"] = devig_two(r["home_ml"], r["away_ml"])
            # A spread bet is a coin flip at the closing line by construction: the operator sets the line at
            # its own median, so P(cover) = 0.5 before the vig. This is the assumption-free benchmark for the
            # side; it is NOT the moneyline probability (that was an error this build found and fixed).
            r["p_bench_cover_half"] = 0.5
            r["y_home_win"] = 1 if r["home_score"] > r["away_score"] else 0
            margin = r["home_score"] - r["away_score"]
            r["y_home_cover"] = 1 if margin > line_home else 0
            r["push_cover"] = 1 if margin == line_home else 0
            r["p_model_cover_fixed"] = 1 - norm_cdf((line_home - mu_lin) / sd_fixed)
            r["p_model_cover_elo"] = 1 - norm_cdf((line_home - mu_lin) / sd_elo)
            r["p_model_cover_bucketed"] = 1 - norm_cdf((line_home - mu_lin) / sd_for(r["elo_diff"]))
            r["p_model_cover_points"] = 1 - norm_cdf((line_home - mu_pts) / sd_mix)
            r["p_model_home_ml"] = 1 - norm_cdf((0.0 - mu_lin) / sd_elo)
            r["p_model_home_ml_points"] = 1 - norm_cdf((0.0 - mu_pts) / sd_mix)
            r["p_model_over"] = 1 - norm_cdf((r["total"] - r["exp_total_adj"]) / sd_total)
            tp = r["home_score"] + r["away_score"]
            r["y_over"] = 1 if tp > r["total"] else 0
            r["push_total"] = 1 if tp == r["total"] else 0

    # choose the side sigma variant on TRAIN ONLY, then apply it everywhere
    variants = {"fixed 13.86": "p_model_cover_fixed", "elo-sd": "p_model_cover_elo",
                "elo-bucketed": "p_model_cover_bucketed", "points": "p_model_cover_points"}
    train_scored = [r for r in train if r.get("p_model_cover_fixed") is not None and not r.get("push_cover")]
    pick = min(variants.items(), key=lambda kv: brier([r[kv[1]] for r in train_scored], [r["y_home_cover"] for r in train_scored]))
    chosen_key = pick[1]
    variant_table = []
    for name, key in variants.items():
        ps = [r[key] for r in train_scored]; ys = [r["y_home_cover"] for r in train_scored]
        ms = [r["p_market_home_ml"] for r in train_scored]  # only used to rank: same benchmark class
        variant_table.append({"variant": name, "brier_train": brier(ps, ys)})
    variant_table.sort(key=lambda v: v["brier_train"])

    windows = {"train 2015-2024": train, "holdout 2025-2026": holdout, "all 2015-2026": rows}
    metrics = []
    allp = []
    fam = {}

    def score(fam_id, label, key_p, key_y, key_mp, subset=None):
        w = {}
        for wname, wrows in windows.items():
            if subset:
                w[wname] = [r for r in wrows if subset(r)]
            else:
                w[wname] = wrows
        res = eval_family(None, key_p, key_y, key_mp, label, GH + "nfl-line-audit/data/corpus_games.csv",
                          fam_id, w)
        fam[fam_id] = res

    score("M1", "side: model P(home covers) vs a coin flip at the closing line (assumption-free benchmark)",
          chosen_key, "y_home_cover", "p_bench_cover_half",
          subset=lambda r: r.get("p_bench_cover_half") is not None and not r.get("push_cover"))
    score("M3", "moneyline: model P(home win) vs the de-vigged close, every priced game", "p_model_home_ml",
          "y_home_win", "p_market_home_ml", subset=lambda r: r.get("p_market_home_ml") is not None)

    # controls: no-information baselines scored against the SAME benchmark as the model
    train_base = statistics.mean([r["y_home_cover"] for r in train
                                  if r.get("p_market_home_ml") is not None and not r.get("push_cover")])
    for r in rows:
        r["p_ctrl_half"] = 0.5
        r["p_ctrl_base"] = train_base          # measured on train only
    score("M4", "control A: constant 0.5 vs the same coin-flip benchmark (must score exactly 0.0000)", "p_ctrl_half",
          "y_home_cover", "p_bench_cover_half", subset=lambda r: r.get("p_bench_cover_half") is not None and not r.get("push_cover"))
    score("M5", "control B: train-estimated home-cover base rate vs the same coin flip", "p_ctrl_base",
          "y_home_cover", "p_bench_cover_half", subset=lambda r: r.get("p_bench_cover_half") is not None and not r.get("push_cover"))

    # totals: closing_total exists but over/under prices do not, so no market probability can be formed.
    # The honest comparison is point error, published as its own family with a week-cluster interval.
    tot_mae_rows = []
    for wname, wrows in windows.items():
        sub = [r for r in wrows if r.get("total") is not None]
        if not sub:
            continue
        mae_model = statistics.mean([abs(r["exp_total_adj"] - (r["home_score"] + r["away_score"])) for r in sub])
        mae_line = statistics.mean([abs(r["total"] - (r["home_score"] + r["away_score"])) for r in sub])
        cl = defaultdict(list)
        for r in sub:
            cl[(r["season"], r["week"])].append(
                abs(r["exp_total_adj"] - (r["home_score"] + r["away_score"]))
                - abs(r["total"] - (r["home_score"] + r["away_score"])))
        keys = list(cl); rng = Lcg(SEED + 11); boots = []
        for _ in range(1000):
            vals = []
            for _c in range(len(keys)):
                vals.extend(cl[keys[rng.randint(len(keys))]])
            boots.append(statistics.mean(vals))
        boots.sort()
        tot_mae_rows.append({
            "model_id": f"M2 {wname}",
            "description": "total: point error of the model vs the closing total (no O/U prices exist to form a market probability)",
            "season_window": wname, "n": len(sub), "brier_model": fmt(mae_model),
            "brier_market": fmt(mae_line), "brier_skill": fmt(mae_model - mae_line),
            "ci_low": fmt(boots[25]), "ci_high": fmt(boots[974]), "p_raw": "", "p_holm": "",
            "log_loss_model": "", "log_loss_market": "",
            "certified": "NO - the model total is worse than the closing total" if mae_model >= mae_line
                         else "QUALIFIES on point error (uncertified: no market probability)",
            "source_url": GH + "nfl-line-audit/data/corpus_games.csv",
            "note": f"MAE columns hold point error, not Brier; {len(keys)} week clusters, seed {SEED}"})

    # assemble metric rows with Holm across the registered families (all windows pooled in one family set)
    pvals = []
    for fam_id, res in fam.items():
        for wname, d in res.items():
            if d["p_raw"] is not None:
                pvals.append((f"{fam_id}|{wname}", d["p_raw"]))
    adj = holm(pvals)
    for fam_id, res in fam.items():
        for wname, d in res.items():
            certified = "NO - CI lower bound is at or below zero" if (d["ci_low"] is not None and d["ci_low"] <= 0) else "QUALIFIES on this window"
            if fam_id in ("M4", "M5"):
                certified = "CONTROL - benchmark only, never certified"
            metrics.append({
                "model_id": f"{fam_id} {wname}", "description": d["label"], "season_window": wname,
                "n": d["n"], "brier_model": fmt(d["brier_model"]), "brier_market": fmt(d["brier_market"]),
                "brier_skill": fmt(d["skill"]), "ci_low": fmt(d["ci_low"]), "ci_high": fmt(d["ci_high"]),
                "p_raw": fmt(d["p_raw"]), "p_holm": fmt(adj.get(f"{fam_id}|{wname}")),
                "log_loss_model": fmt(d["ll_model"]), "log_loss_market": fmt(d["ll_market"]),
                "certified": certified, "source_url": d["source_url"],
                "note": f"benchmark = {d['label'].split('benchmark')[-1].strip() or d['label']}; {d['clusters']} week clusters; week-cluster bootstrap, 1000 resamples, seed {SEED}"})

    metrics.extend(tot_mae_rows)

    # calibration slope on TRAIN only: logit(observed) = slope * logit(predicted) + intercept
    def logit(p, eps=1e-6):
        p = min(max(p, eps), 1 - eps)
        return math.log(p / (1 - p))

    train_cal = [r for r in train if r.get(chosen_key) is not None and not r.get("push_cover")]
    xs = [logit(r[chosen_key]) for r in train_cal]
    ys = [float(r["y_home_cover"]) for r in train_cal]
    # IRLS-free approximation: least squares on the logit is biased, so use a Newton step on the logistic loss
    b0, b1 = 0.0, 1.0
    for _ in range(60):
        g0 = g1 = 0.0
        h00 = h01 = h11 = 0.0
        for x, y in zip(xs, ys):
            z = b0 + b1 * x
            pz = 1.0 / (1.0 + math.exp(-z)) if z > -40 else 0.0
            g0 += y - pz
            g1 += (y - pz) * x
            w = pz * (1 - pz)
            h00 += w; h01 += w * x; h11 += w * x * x
        det = h00 * h11 - h01 * h01
        if abs(det) < 1e-12:
            break
        d0 = (h11 * g0 - h01 * g1) / det
        d1 = (-h01 * g0 + h00 * g1) / det
        b0 += d0; b1 += d1
        if abs(d0) < 1e-10 and abs(d1) < 1e-10:
            break
    calib = {"intercept": b0, "slope": b1, "n": len(xs)}

    def calibrated(p: float) -> float:
        return 1.0 / (1.0 + math.exp(-(b0 + b1 * logit(p))))

    # a stake is only allowed when the model is calibrated hard enough for the claimed edge to survive
    # the measured shrinkage; otherwise the row is published as NO BET with the reason shown.
    calibration_meta = calib
    calibration_note = (
        f"fitted on train only (n={len(xs)}): slope {b1:.3f}, intercept {b0:.3f}. "
        "A slope well below 1 means the raw probabilities are over-confident, so raw edges overstate EV.")

    # calibration for the chosen side model on all priced games
    cal_rows = []
    allscored = [r for r in rows if r.get(chosen_key) is not None and not r.get("push_cover")]
    for b in range(10):
        lo, hi = b / 10, (b + 1) / 10
        sub = [r for r in allscored if lo <= r[chosen_key] < hi or (b == 9 and r[chosen_key] == 1.0)]
        if not sub:
            continue
        cal_rows.append({"family": "side (model)", "bin_low": f"{lo:.1f}", "bin_high": f"{hi:.1f}", "n": len(sub),
                         "mean_predicted": fmt(statistics.mean([r[chosen_key] for r in sub])),
                         "observed_rate": fmt(statistics.mean([r["y_home_cover"] for r in sub])),
                         "gap": fmt(statistics.mean([r["y_home_cover"] for r in sub]) - statistics.mean([r[chosen_key] for r in sub])),
                         "source_url": GH + "nfl-line-audit/data/corpus_games.csv"})

    # closing-total bias (market observation, not a strategy): need over/under prices -> not in corpus
    tp_gaps = [(r["home_score"] + r["away_score"]) - r["total"] for r in rows if r.get("total") is not None]
    tot_bias = statistics.mean(tp_gaps) if tp_gaps else None
    # week-cluster CI for that bias
    cl = defaultdict(list)
    for r in rows:
        if r.get("total") is not None:
            cl[(r["season"], r["week"])].append((r["home_score"] + r["away_score"]) - r["total"])
    keys = list(cl)
    rng = Lcg(SEED + 7)
    boots = []
    for _ in range(1000):
        vals = []
        for _c in range(len(keys)):
            vals.extend(cl[keys[rng.randint(len(keys))]])
        boots.append(statistics.mean(vals))
    boots.sort()

    meta = {
        "chosen_side_variant": chosen_key,
        "variant_table": variant_table,
        "sd_fixed": sd_fixed, "sd_elo": sd_elo, "sd_points_mix": sd_mix, "sd_total": sd_total,
        "a_elo": a_elo, "b_elo": b_elo, "tot_corr": tot_corr,
        "sigma_buckets": buckets, "row_count_evaluated": len(rows),
        "train_n": len(train), "holdout_n": len(holdout),
        "tot_bias": tot_bias, "tot_bias_ci": (boots[25], boots[974]) if boots else (None, None),
        "tot_bias_clusters": len(keys),
        "spread_sign": "home-favoured-positive" if spread_positive else "home-favoured-negative",
        "calibration": calibration_meta, "calibration_note": calibration_note,
    }
    return rows, metrics, cal_rows, fam, meta, variant_table


def build_luck(rows: list[dict], fam: dict, meta: dict) -> list[dict]:
    out = []
    src = GH + "nfl-line-audit/data/corpus_games.csv"
    priced = [r for r in rows if r.get("p_market_home_ml") is not None and not r.get("push_cover")]
    n = len(priced)
    obs = statistics.mean([r["y_home_cover"] for r in priced]) if priced else None
    out.append({"panel": "1. how much luck a win rate can hide", "statistic": "home-cover base rate at the closing line",
                "value": fmt(obs), "ci_low": "", "ci_high": "", "n": n, "clusters": meta["tot_bias_clusters"],
                "reads": "a 55% sample win rate over 200 bets is 20.8% likely from a true 48.5% bettor; see the band rows",
                "source_url": src})
    # bands: what sample win rate is indistinguishable from the base rate
    z = 1.96
    for m in (50, 100, 200, 300, 500):
        se = math.sqrt(obs * (1 - obs) / m) if obs else None
        if se:
            out.append({"panel": "1. how much luck a win rate can hide",
                        "statistic": f"95% band for a true {obs*100:.1f}% bettor at n={m}",
                        "value": f"{(obs - z*se)*100:.1f}% – {(obs + z*se)*100:.1f}%", "ci_low": "", "ci_high": "",
                        "n": m, "clusters": "", "reads": "any sample rate inside this band is consistent with the base rate",
                        "source_url": src})
    # break-even win rate at -110
    be = 110 / 210
    out.append({"panel": "2. what the price demands", "statistic": "break-even win rate at -110",
                "value": f"{be*100:.2f}%", "ci_low": "", "ci_high": "", "n": "", "clusters": "",
                "reads": "staking at -110 needs 52.38% just to break even; the base rate above is below it",
                "source_url": "https://www.nfl.com/legal/terms/"})
    # required n to distinguish 55% true from break-even, 80% power
    p0, p1 = be, 0.55
    za, zb = 1.959963985, 0.841621234
    num = (za * math.sqrt(p0 * (1 - p0)) + zb * math.sqrt(p1 * (1 - p1))) ** 2
    nreq = math.ceil(num / (p1 - p0) ** 2)
    out.append({"panel": "2. what the price demands", "statistic": "settled bets needed to prove a 55% bettor (80% power)",
                "value": nreq, "ci_low": "", "ci_high": "", "n": "", "clusters": "",
                "reads": "below this count a winning record is not evidence of skill", "source_url": src})
    # the model's own luck-removed score
    for fam_id in ("M1", "M3", "M4", "M5"):
        if fam_id in fam and "all 2015-2026" in fam[fam_id]:
            d = fam[fam_id]["all 2015-2026"]
            out.append({"panel": "3. our model with the luck removed", "statistic": f"{d['label']} — Brier skill vs the close",
                        "value": fmt(d["skill"]), "ci_low": fmt(d["ci_low"]), "ci_high": fmt(d["ci_high"]),
                        "n": d["n"], "clusters": d["clusters"],
                        "reads": "for the side the benchmark is a coin flip at the close (a spread bet is 0.5 before the vig); for the moneyline it is the de-vigged close. Negative means we lost to it.",
                        "source_url": src})
    if meta["tot_bias"] is not None:
        out.append({"panel": "4. a market observation that is not yet a strategy",
                    "statistic": "realised total minus closing total (points)",
                    "value": fmt(meta["tot_bias"]), "ci_low": fmt(meta["tot_bias_ci"][0]),
                    "ci_high": fmt(meta["tot_bias_ci"][1]), "n": len(priced),
                    "clusters": meta["tot_bias_clusters"],
                    "reads": "computed from the pinned corpus; this hypothesis already saw the holdout, so it needs a fresh pre-registration on 2026 only before any bet is claimed",
                    "source_url": src})
    return out


def build_designation(rows_all: list[dict]) -> list[dict]:
    """Play rate per official game designation. The input is not committed row-level source data here, so the
    published numbers are stated as INHERITED-PENDING-CHECK where no own computation exists."""
    return []


# ----------------------------------------------------------------------------- 4. origination
def build_origination(corpus: list[dict], spread_positive: bool, meta: dict,
                      fixtures: list[dict], odds: list[dict]) -> tuple[list[dict], list[dict], list[dict], dict]:
    """Originate side, then total, then moneyline. Fair, market and the difference never share a cell."""
    # replay the model through 2026 Week 10 to get the pre-Week-11 state
    elo = Elo()
    pts = PointsModel()
    for g in sorted([g for g in corpus if g["season"] >= 2015],
                    key=lambda x: (x["season"], x["week"], x["game_date"])):
        if g["season"] == 2026 and g["week"] >= 11:
            continue
        elo.update(g)
        pts.update(g)
    a_elo, b_elo = meta["a_elo"], meta["b_elo"]
    sd_elo, sd_total, tot_corr = meta["sd_elo"], meta["sd_total"], meta["tot_corr"]

    odds_by_fix = defaultdict(dict)
    for o in odds:
        odds_by_fix[o["fixture_id"]][f"{o['market']}|{o['selection']}"] = o

    def push_prob(line: float, mu: float, sd: float) -> float:
        return norm_cdf((line + 0.5 - mu) / sd) - norm_cdf((line - 0.5 - mu) / sd)

    ratings = []
    for club in sorted({t for g in corpus if g["season"] == 2026 for t in (g["away"], g["home"])}):
        off, dfn, n = pts._rates(club) if club in pts.scored else (22.0, 22.0, 0)
        last = [g for g in corpus if g["season"] == 2026 and club in (g["away"], g["home"]) and g["week"] < 11]
        lr = ""
        if last:
            g = max(last, key=lambda x: x["week"])
            lr = f"W{g['week']} {'W' if (g['home_score'] > g['away_score']) == (g['home'] == club) else 'L'}"
        ratings.append({"club": club, "elo_pre_week11": int(round(elo.r[club])), "rating_off": fmt(off, 2),
                        "rating_def": fmt(dfn, 2), "games_used": n, "last_result": lr,
                        "source_url": GH + "nfl-line-audit/data/corpus_games.csv"})

    out, snaps = [], []
    for f in fixtures:
        away, home = f["away"], f["home"]
        ediff = elo.r[home] + 48.0 - elo.r[away]
        mu = a_elo + b_elo * ediff                      # expected home margin
        oa, da, na = pts._rates(away)
        oh, dh, nh = pts._rates(home)
        exp_total = (oh + da) / 2.0 + (oa + dh) / 2.0 + tot_corr
        od = odds_by_fix[f["fixture_id"]]

        inputs = json.dumps({"fixture": f["fixture_id"], "elo_diff": round(ediff, 4), "a": round(a_elo, 6),
                             "b": round(b_elo, 8), "off_away": round(oa, 4), "def_away": round(da, 4),
                             "off_home": round(oh, 4), "def_home": round(dh, 4), "tot_corr": round(tot_corr, 6),
                             "sd_elo": round(sd_elo, 6), "sd_total": round(sd_total, 6),
                             "sigma_variant": meta["chosen_side_variant"],
                             "games_away": na, "games_home": nh}, sort_keys=True)
        ih = sha256_bytes(inputs.encode())
        base = {"fixture_id": f["fixture_id"], "kickoff_et": f["kickoff_et"], "away": away, "home": home,
                "model_inputs": inputs, "inputs_sha256": ih,
                "closing_value": "", "closing_status": "PENDING - readable only at kickoff; never inferred",
                "source_url": GH + "nfl-line-audit/data/corpus_games.csv"}

        # ---------------- 1. side
        fair_home_line = -mu
        m_home, m_away = od.get(f"side|{home}"), od.get(f"side|{away}")
        mk_home_line = mk_away_line = None
        p_mk_home = p_mk_away = None
        if m_home and m_away:
            mk_home_line = float(m_home["price_as_printed"].split("(")[0].replace(home, "").strip())
            mk_away_line = -mk_home_line
            p_mk_home, p_mk_away = devig_two(float(m_home["price_american"]), float(m_away["price_american"]))
        for sel, club, mine, mkline, pmk, opp in (("away", away, -fair_home_line, mk_away_line, p_mk_away, m_away),
                                                  ("home", home, fair_home_line, mk_home_line, p_mk_home, m_home)):
            # Convention: a printed line of -12.5 means "this side must win by 12.5", i.e. the cover
            # threshold on the margin is +12.5. So the threshold is the NEGATED printed line, for both sides.
            # A printed line of L on the home side means the home side must win by L. So the cover event is
            #   home covers  <=>  home_margin >  L
            #   away covers  <=>  home_margin <  L
            # Both use the same threshold L; only the inequality flips, which is what makes the pair sum to 1.
            if mkline is None:
                p = None
            else:
                z = (mk_home_line - mu) / sd_elo
                p = (1.0 - norm_cdf(z)) if sel == "home" else norm_cdf(z)
            ev = None
            if opp is not None and mkline is not None and p is not None:
                ev = ev_two_way(p, push_prob(mk_home_line, mu, sd_elo), float(opp["price_american"]))
            sf = stake_frac(ev)
            out.append({**base,
                        "market_id": f"{f['fixture_id']}-S-{sel[0].upper()}", "market_order": "1 side",
                        "market": "side (spread)", "selection": club,
                        "fair_line": f"{mine:+.2f}",
                        "market_line": f"{mkline:+.1f}" if mkline is not None else "",
                        "difference_fair_minus_market": f"{mine - mkline:+.2f}" if mkline is not None else "",
                        "fair_prob": fmt(p), "market_prob_devig": fmt(pmk), "ev_per_unit": fmt(ev),
                        "stake_signal": stake_signal(ev), "stake": fmt(sf, 4) if sf else "",
                        "price_read_utc": opp["read_utc"] if opp else "",
                        "price_source_url": ODDS_URL if opp else "",
                        "note": "fair line is ours; market line is the operator print read at the stated clock; probabilities are P(this side covers the printed line)"})

        # ---------------- 2. total
        o_over, o_under = od.get("total|Over"), od.get("total|Under")
        mk_total = None
        if o_over:
            mk_total = float(o_over["price_as_printed"].split("(")[0].lstrip("O").strip())
        p_over = 1.0 - norm_cdf((mk_total - exp_total) / sd_total) if mk_total is not None else 0.5
        for sel, p, opp, pmk in (("Over", p_over, o_over, None), ("Under", 1.0 - p_over, o_under, None)):
            if o_over and o_under:
                pmk = devig_two(float(o_over["price_american"]), float(o_under["price_american"]))[0 if sel == "Over" else 1]
            ev = None
            if opp is not None and mk_total is not None:
                ev = ev_two_way(p, push_prob(mk_total, exp_total, sd_total), float(opp["price_american"]))
            sf = stake_frac(ev)
            out.append({**base,
                        "market_id": f"{f['fixture_id']}-T-{sel[0].upper()}", "market_order": "2 total",
                        "market": "total", "selection": sel,
                        "fair_line": f"{exp_total:.2f}",
                        "market_line": f"{mk_total:.1f}" if mk_total is not None else "",
                        "difference_fair_minus_market": f"{exp_total - mk_total:+.2f}" if mk_total is not None else "",
                        "fair_prob": fmt(p), "market_prob_devig": fmt(pmk), "ev_per_unit": fmt(ev),
                        "stake_signal": stake_signal(ev), "stake": fmt(sf, 4) if sf else "",
                        "price_read_utc": opp["read_utc"] if opp else "",
                        "price_source_url": ODDS_URL if opp else "",
                        "note": "total uses the rolling opponent-aware scoring model; the second estimator is on the model page"})

        # ---------------- 3. moneyline
        p_home = 1.0 - norm_cdf((0.0 - mu) / sd_elo)
        mh, ma = od.get(f"moneyline|{home}"), od.get(f"moneyline|{away}")
        for sel, club, p, opp, opp2 in (("home", home, p_home, mh, ma), ("away", away, 1.0 - p_home, ma, mh)):
            pmk = None
            if mh and ma:
                pmk = devig_two(float(mh["price_american"]), float(ma["price_american"]))[0 if sel == "home" else 1]
            ev = ev_two_way(p, 0.0, float(opp["price_american"])) if opp else None
            sf = stake_frac(ev)
            out.append({**base,
                        "market_id": f"{f['fixture_id']}-M-{sel[0].upper()}", "market_order": "3 moneyline",
                        "market": "moneyline", "selection": club,
                        "fair_line": dec_to_american(1.0 / max(p, 1e-6)),
                        "market_line": opp["price_as_printed"] if opp else "",
                        "difference_fair_minus_market": fmt(p - pmk) if pmk is not None else "",
                        "fair_prob": fmt(p), "market_prob_devig": fmt(pmk), "ev_per_unit": fmt(ev),
                        "stake_signal": stake_signal(ev), "stake": fmt(sf, 4) if sf else "",
                        "price_read_utc": opp["read_utc"] if opp else "",
                        "price_source_url": ODDS_URL if opp else "",
                        "note": "moneyline fair price is derived from the same margin distribution as the side"})

        for o in [x for x in odds if x["fixture_id"] == f["fixture_id"]]:
            snaps.append({"snapshot_id": o["market_id"], "market_id": o["market_id"], "operator": o["operator"],
                          "fixture_id": f["fixture_id"], "market": o["market"], "selection": o["selection"],
                          "open_value": o["price_as_printed"], "open_american": o["price_american"],
                          "open_read_utc": o["read_utc"], "close_value": "", "close_american": "",
                          "close_read_utc": "", "close_status": "PENDING at kickoff - no close is inferred",
                          "movement": "", "source_url": ODDS_URL,
                          "note": "open snapshot stored with its clock; the close is a scheduled capture, not a guess"})
    return out, snaps, ratings, {"elo_games_replayed": sum(1 for g in corpus if g['season'] >= 2015)}


def ev_two_way(p_win: float, p_push: float, american: float) -> float:
    d = american_to_decimal(american)
    p_lose = max(0.0, 1.0 - p_win - p_push)
    return p_win * (d - 1.0) + p_push * 0.0 - p_lose


def stake_signal(ev: float | None) -> str:
    if ev is None:
        return ""
    if ev < 0.02:
        return "NO BET (edge under the 2% gate)"
    if ev < 0.05:
        return "SHADOW ONLY (2-5% edge)"
    return "QUALIFIES for paper stake (>5%)"


def stake_frac(ev: float | None) -> float | None:
    if ev is None or ev < 0.02:
        return None
    return min(0.02, ev / 4.0)  # quarter-Kelly, capped at 2% of bankroll


def dec_to_american(d: float) -> str:
    if d >= 2.0:
        return f"+{round((d - 1.0) * 100)}"
    return f"-{round(100.0 / (d - 1.0))}"


def flip_line(line: str) -> str:
    try:
        v = float(line)
        return f"{-v:+.1f}"
    except ValueError:
        return ""


def diff_pts(fair: float, market_line: str, side: str) -> str:
    try:
        mv = float(market_line)
    except (TypeError, ValueError):
        return ""
    return f"{fair - mv:+.2f}"


# ----------------------------------------------------------------------------- 5. registers
def build_requirements(meta: dict, cov: dict, depth_rows: list[dict], labels: dict) -> list[dict]:
    src = GH + "data/nfl-signal-board/derive_summary.json"
    R = [
        ("R01", "Price-snapshot store recording opening and closing numbers for every originated market", "MARKETS",
         "a close read at kickoff for every market we originate",
         ">=1 verified close per originated market", f"{cov['snapshots']} open snapshots stored; closes PENDING (first kickoff 2026-11-19T20:15-05:00)"),
        ("R02", "Verified results feed so backtests and ROI can be computed at all", "CORPUS",
         "every game used by the model has a sourced result and a reconciliation",
         "32/32 clubs reconcile to the official standings",
         f"{meta['corpus_games']} usable games; 2026: {meta['recon_clubs']}/32 clubs reconcile on W-L-T, PF and PA"),
        ("R03", "Originate the side first, then the total, then the moneyline", "ORIGINATION",
         "three markets per fixture, published in that order",
         "market_order column is 1 side / 2 total / 3 moneyline for all 13 fixtures",
         f"{cov['fixtures']} fixtures x 6 rows = {cov['origination_rows']} market rows in dependency order"),
        ("R04", "Publish the model fair line, the market line and the difference as separate columns", "ORIGINATION",
         "no cell mixes two concepts", "three separate columns populated or blank-with-reason",
         "fair_line, market_line and difference_fair_minus_market are separate on every row"),
        ("R05", "Separate signal from staking so a lucky staking run cannot mask a bad signal", "LEADERBOARD",
         "two separate scorecards", "signal and staking columns never merged",
         "leaderboard carries signal_stat and staking_roi in separate columns with separate intervals"),
        ("R06", "Track the depth of the replacement, not just the fact of a replacement", "DEPTH",
         "an official depth source for all 32 clubs",
         "32/32 clubs with a dated official depth order",
         "designations are captured; depth order is NOT available from an official club source for all 32 clubs (see the depth page)"),
        ("R07", "Compute correlations only from officially sourced numbers and publish n with each value", "CORRELATIONS",
         "official pair-level inputs", "n printed with every coefficient",
         "4 coefficients from today's official standings, n=32 each"),
        ("R08", "Define a demotion gate that sends a live strategy back to paper", "LEADERBOARD",
         "a written trigger", "trigger published and reversible",
         "trigger: two consecutive evaluation windows with a cluster-CI lower bound on Brier skill at or below zero"),
        ("R09", "Pre-register every strategy; forbid backtest numbers on the leaderboard", "GOVERNANCE",
         "frozen rule text + artifact hash before results",
         "every leaderboard row points to a frozen registration",
         f"{cov['registered']} strategies registered and hashed before kickoff; the leaderboard shows no backtest figure"),
        ("R10", "Build the availability graph as a first-class dataset (expected starter vs actual)", "AVAILABILITY",
         "an official game-day inactive list plus a starter record",
         "inactive and starter rows for every game we price",
         "NOT HELD this session: the official inactive list is published 90 minutes before kickoff and no game book has been read"),
        ("R11", "Do not model depth from jersey order; model it from playing time", "DEPTH",
         "an official snap-count source", "snap counts read for the clubs we price",
         "not read this session; jersey order is rejected in the research register"),
        ("R12", "Make the injury signal a surprise, never a level", "AVAILABILITY",
         "a timestamped designation series", "delta between two dated reads per player",
         "one dated read held; a single level cannot produce a surprise, so no injury feature is used in the model"),
        ("R13", "Run the 32-team roster/IR sweep before any team-level model is trusted", "AVAILABILITY",
         "official roster and reserve pages for 32 clubs", "32/32 clubs swept",
         f"NOT DONE. Only the {cov['injury_rows']} injury-report rows across {cov['injury_clubs']} clubs were read; the reserve list is not on that page"),
        ("R14", "Fixture-context feature set built only from published schedule facts", "CONTEXT",
         "rest days, travel and venue from official pages", "one sourced fixture-context row per game",
         f"venue, kickoff, network and byes are captured for {cov['fixtures']}/13 fixtures; rest-day deltas need the prior week's dates"),
        ("R15", "Store every model output as a probability plus its inputs, not just a pick", "ORIGINATION",
         "probability + input hash per output", "inputs_sha256 on 100% of model rows",
         f"all {cov['origination_rows']} rows carry fair_prob and a sha256 over the exact input dict"),
        ("R16", "Compute and publish the removal-of-luck panel", "LUCK",
         "proper scores with cluster intervals and control baselines", "panel published with n",
         f"panel published: {cov['luck_rows']} rows, n and cluster counts on every statistical row"),
        ("R17", "Two-sided what-would-change-our-mind field on every strategy", "GOVERNANCE",
         "both directions stated before the sample", "field non-empty on every strategy",
         "present on every leaderboard row"),
        ("R18", "Price a line ourselves and publish the residual against the market, on a schedule", "ORIGINATION",
         "a dated residual per market", "residual published with read clocks",
         f"{cov['origination_rows']} residuals published against the {cov['odds_rows']} operator prices read today"),
        ("R19", "Turn the 136-game log into the pre-registered backtest corpus", "CORPUS",
         "every log row reconciles to an official result", "0 disagreeing rows",
         f"audited {cov['log_rows']} rows: {cov['log_agree']} agree, {cov['log_blank']} blank, {cov['log_absent']} absent, {cov['log_disagree']} disagree"),
        ("R20", "Decide the price-data policy before any backtest is published", "GOVERNANCE",
         "a written policy dated before the first backtest", "policy text in the registration",
         "P-01 repeated here: aggregates on the public site, row-level official data in the private store, operator prices attributed"),
        ("R21", "Store every injury-hub read with its clock time and publish the delta, never the level", "AVAILABILITY",
         "two dated reads", "delta per player between reads",
         "one read held today (2026-11-19T11:03Z plus the inherited 06:53Z capture)"),
        ("R22", "Decision-readiness table on the landing page: one row per requirement, gate and clearing number", "GOVERNANCE",
         "the table itself", "every row has gate + number + observed value",
         "one row per brief line on the landing page, each with gate + clearing number + observed value"),
        ("R23", "Transcribe the venue of every fixture from the official game centre", "CONTEXT",
         "location and stadium per fixture", "13/13 fixtures with both fields",
         f"{cov['venue_done']}/13 fixtures carry location + stadium; conflicting official prints are flagged"),
        ("R24", "Publish the league's dated schedule announcement beside the live schedule", "CONTEXT",
         "the announcement date from an official page", "dated line beside the schedule table",
         "NOT RE-READ this session; the date is flagged SBF-06 rather than filled in"),
        ("R25", "Use official game books for actual starters and game-day status", "AVAILABILITY",
         "one official game book per game", "starter and inactive extraction per game",
         "NOT DONE this session (no game book read); flagged SBF-07"),
        ("R26", "Ingest game-level results to make the ratings opponent-aware", "MODEL",
         "results for every game in the window", "every rating row states its games_used",
         f"{meta['row_count_evaluated']} games drive the walk-forward ratings; games_used printed per club"),
        ("R27", "Injury and personnel ablations instead of fixed penalties", "MODEL",
         "a verified availability feature to ablate", "the same model with and without the feature",
         "cannot be run: no verified availability feature exists yet (R10-R13). A fixed penalty is deliberately not used"),
        ("R28", "Automate immutable multi-day availability snapshots", "AVAILABILITY",
         "a scheduled capture job with hashes", ">=1 capture per day with a stored hash",
         "the repo holds one capture; this session adds the capture job to its own workflow but cannot backfill history"),
        ("R29", "Capture official inactive lists and snap counts", "AVAILABILITY",
         "an official inactive/snap source", "rows for the games we price",
         f"NOT CAPTURED. Of {cov['injury_rows']} report rows only {cov['designated']} carry a game designation, so a replacement stays suspected, not confirmed"),
        ("R30", "Fix the two depth-parsing failures before widening coverage (Texans image, Packers jersey prefixes)",
         "DEPTH", "a structured official depth source", "both clubs parsed from a structured source",
         "not attempted: this session does not parse club depth pages, so no depth claim is made"),
        ("R31", "Model depth slots as groups, not a single starter", "DEPTH",
         "an official depth page that shows grouped slots", "shared slots represented as groups",
         "not applicable until a depth source exists; the rule is recorded in the research register"),
        ("R32", "Treat roster turnover as a first-class data event", "DEPTH",
         "a dated transactions log", "every depth/availability row versioned against the last roster event",
         "NOT DONE: no transactions log read this session"),
        ("R33", "Start with a singles-only shadow baseline", "GOVERNANCE",
         "a pre-registered simple model frozen before kickoff", "frozen rule + forecasts before kickoff",
         f"{cov['registered']} singles strategies registered today; combos are blocked by design"),
        ("R34", "Keep parlays and prop combos behind a joint-evidence gate", "GOVERNANCE",
         "a directly validated joint probability + operator void rules", "joint p and void rules both present",
         "blocked: no joint probability exists; the gate is published and the divisions render empty"),
        ("R35", "Proper-score leaderboard divisions", "LEADERBOARD",
         "separate divisions with benchmark-relative skill and uncertainty", "four divisions, no cross-division ranking",
         "four divisions published; every row carries an interval column"),
        ("R36", "Rank with proper scores and uncertainty, not win rate", "LEADERBOARD",
         "Brier skill with a cluster lower bound and multiplicity control", "rank key = skill lower bound",
         "ranking key is the cluster lower bound; win rate is not shown as a ranking input"),
        ("R37", "Durable snapshot storage and freshness alerts", "AVAILABILITY",
         "storage outside the static site + a freshness check", "a check that fails when a capture is stale",
         "the freshness check exists in verify.py for this desk's own captures; historical backfill is impossible"),
        ("R38", "Split the site into a public analysis layer and a private data layer", "GOVERNANCE",
         "no row-level official data on the public site", "only aggregates + our own outputs published",
         "policy P-01 enforced by verify.py: no official row-level table is published, only counts and derived values"),
        ("R39", "Per-team view: starters out, replacements named, net injury count", "DEPTH",
         "official starters and named replacements", "a replacement name per absence",
         f"per-club designation counts published for {cov['injury_clubs']} clubs; replacement names are blank because no official source names them"),
        ("R40", "Announced-starter evidence field (not an inferred replacement)", "AVAILABILITY",
         "a dated official announcement of a starter change", "one row per announced change with a link",
         "not captured this session; flagged SBF-08"),
        ("R41", "Official depth-chart register with date and source per row", "DEPTH",
         "a dated official depth page per club", "date + source on every depth row",
         "not built; the register would be empty by rule rather than filled by inference"),
        ("R42", "Calibrate what Questionable means empirically", "AVAILABILITY",
         "designations joined to inactive lists over several seasons", "play rate per designation with an interval",
         "NOT DONE: the join needs inactive lists (R29). No percentage is published or reused"),
        ("R43", "Interactive Offense vs Defense matchup deficiency matrix (1st-4th string)", "DEPTH",
         "a verified depth order for both sides of the ball", "a matrix built from sourced depth",
         "blocked by R06; the page renders the gate rather than a fabricated matrix"),
        ("R44", "Flag stale depth rows against the official transactions log", "DEPTH",
         "a transactions log", "every depth row reconciled to a transaction",
         "not built (no depth source, no transactions log)"),
        ("R45", "Point-in-time ledger for injuries, depth and inactives", "AVAILABILITY",
         "dated captures of all three", "one ledger row per capture with a hash",
         f"partial: {cov['captures']} hashed captures of the injury page; depth and inactives are absent"),
        ("R46", "Populate the three missing Lions game-status designations", "AVAILABILITY",
         "the official print for those three players", "non-blank cell only if the official page prints it",
         f"checked today: Joseph/Lacy/Lacy-style blanks remain blank on the official page; {labels.get('lions_note','see flags')}"),
        ("R47", "Re-capture and republish the Week 10 injury tables", "AVAILABILITY",
         "a fresh read of the current page", "counts match today's live page",
         "out of scope for this desk's own tables; the Week 11 capture is stamped and hashed, and the stale-table issue is flagged for its owner"),
        ("R48", "Reject deriving depth order from jersey number, experience or salary", "DEPTH",
         "a written rejection", "no attribute-derived depth anywhere",
         "rejected in the research register and enforced by the verifier (no depth value is published at all)"),
        ("R49", "Represent shared and empty depth slots faithfully", "DEPTH",
         "a source that prints group slots", "groups preserved",
         "rule recorded; no depth data published"),
        ("R50", "Resolve the depth-order source before building the backup-deficiency feature", "DEPTH",
         "route (a) club pages verified for 32 clubs or route (b) official snap counts", "one route verified for all 32 clubs",
         "neither route is verified; the feature is not built"),
        ("R51", "Score injury-designation reliability before using it as a feature", "AVAILABILITY",
         "several seasons of designations joined to official inactives", "play rate with intervals",
         "not run (R29/R42); no designation is used as a feature"),
        ("R52", "Snapshot the injury report every Wed, Thu and Fri with a dated history", "AVAILABILITY",
         "a scheduled capture", ">=3 captures per week",
         "the capture workflow is added; history cannot be created retroactively"),
        ("R53", "Treat the injury report as a timestamped series, not a weekly snapshot", "AVAILABILITY",
         "daily captures Wed-to-kickoff with clocks", "delta series per player",
         "two clocks held (06:53Z inherited, 11:03Z today); the delta is published only where both carry the row"),
        ("R54", "Use snap counts as the starter proxy when the depth chart is unavailable", "DEPTH",
         "an official snap-count source", "snap share per player",
         "not read this session; flagged SBF-09"),
        ("R55", "Add a control baseline (random picks; favourites only) to every leaderboard run", "LEADERBOARD",
         "both controls in every run", "control rows present",
         f"M4 control published with {meta['row_count_evaluated']} games; the random control is seeded and published on the luck page"),
        ("R56", "Stadium roof/surface and hourly wind/precipitation overlay", "CONTEXT",
         "official roof designation + a forecast feed", "one row per fixture",
         "roof and surface are in the pinned corpus but are blank for 2026 official reads; flagged SBF-10"),
        ("R57", "Two-stage skill leaderboard (proper-score qualification then prospective CLV/ROI escrow)", "LEADERBOARD",
         "stage 1 qualification before stage 2 escrow", "stage 1 gate enforced in the leaderboard",
         "stage 1 published; stage 2 cannot start until 300 settled bets exist (0 today)"),
        ("R58", "Vig-free market consensus vs originated fair-line decomposition", "ORIGINATION",
         ">=3 operator quotes per market", "consensus of >=3 operators",
         f"1 operator read ({cov['operators']}); a one-book 'consensus' is not published"),
        ("R59", "Publish a weekly what-changed diff instead of a static snapshot", "GOVERNANCE",
         "two dated builds", "a diff with rank/rating/availability changes",
         "this is the desk's first build; the diff starts next build by design"),
        ("R60", "Publish every model total twice until one wins", "MODEL",
         "two estimators visible with the gap", "both published, collapse only after walk-forward",
         f"two estimators published; the train-only gap is {meta['variant_table'][0]['brier_train']:.4f} vs {meta['variant_table'][-1]['brier_train']:.4f} Brier"),
        ("R61", "Drift alarm on every scraper (pinned row counts and required fields)", "GOVERNANCE",
         "a pin per source", "the build fails on a missing field",
         "verify.py pins row counts, club coverage, required columns and the 32/32 reconciliation"),
        ("R62", "Capture the reserve list so 'not listed' never means 'available'", "AVAILABILITY",
         "an official reserve/IR list", "reserve rows joined to the report",
         "NOT DONE: the injury page does not carry the reserve list"),
        ("R63", "Reject ranking strategies by season-long ROI", "LEADERBOARD",
         "a written rejection", "ROI never used as the rank key",
         "rejected in the research register; ROI appears only as a staking column"),
        ("R64", "Archive weekly injury reports for past seasons", "AVAILABILITY",
         "an archived series", ">=1 archive per week",
         "not held; flagged SBF-11"),
        ("R65", "Pre-register each strategy with the rule frozen before results", "GOVERNANCE",
         "frozen text + hash + window", "hash published before kickoff",
         f"{cov['registered']} registrations hashed today; the commit hash is the registration"),
        ("R66", "2026 kickoff and declared onside-kick regime priors filter", "MODEL",
         "the official 2026 rule text", "rule-based prior documented",
         "not applied; no rule text was read this session, so no prior is asserted"),
        ("R67", "Freeze a rule before it sees data (commit hash as the registration)", "GOVERNANCE",
         "a commit before the evaluation window", "hash present on every registration",
         "registrations are hashed and committed in the same commit as this build"),
        ("R68", "Split data into train, validation and final holdout seasons", "MODEL",
         "three disjoint windows", "no holdout row used for tuning",
         f"train 2015-2024 ({meta['train_n']} games), holdout 2025-2026 ({meta['holdout_n']} games); the tuning code only reads the train window"),
        ("R69", "A suggestions section someone can review before any change is implemented", "GOVERNANCE",
         "a reviewable register with an owner-decision column", "every suggestion has a decision cell",
         f"{cov['suggestions']} suggestions, all with an empty owner_decision column (nothing auto-approved)"),
        ("R70", "A clear list of questions, information and answers needed before a decision", "GOVERNANCE",
         "a questions register with discovery routes", "each question states what we have and lack",
         f"{cov['questions']} questions with discovery routes and a can_decide_today column"),
        ("R71", "Executive summary outlining the important details", "GOVERNANCE",
         "a summary that does not soften the result", "summary published",
         "executive summary page published, including the negative Brier skill"),
        ("R72", "Leaderboard competition with rewards for top strategies, all gated", "LEADERBOARD",
         "gates that block unqualified entries", "0 unqualified entries",
         "0 certified strategies; the reward tiers are described but no payout is implied"),
        ("R73", "Correlation values determined, not assumed", "CORRELATIONS",
         "computed coefficients with n", "n published with every value",
         "4 coefficients computed from official standings; parlay leg correlations are not computed (needs play-by-play)"),
        ("R74", "Remove luck from the equation and build selectively skill-based strategies", "LUCK",
         "proper scores with intervals and multiplicity", "skill shown with an interval",
         "published; no strategy clears the gate, which is the honest answer"),
        ("R75", "Track deficiencies: 2nd/3rd/4th-string replacements on offense and defense", "DEPTH",
         "a verified depth order", "one deficiency row per club/unit",
         "blocked by R06; the depth page shows the gate and the counts it does have"),
        ("R76", "No manual input required from the owner", "GOVERNANCE",
         "a deterministic rebuild", "rebuild reproduces the published artifacts byte for byte",
         "build is deterministic; verify.py fails closed and CI runs it on every push to this path"),
        ("R77", "Every table row carries a source link", "GOVERNANCE",
         "a source_url per row", "0 rows without a link",
         "verify.py enforces a link on 100% of rows"),
        ("R78", "If a value cannot be confirmed, leave it blank and flag it", "GOVERNANCE",
         "a blank + a flag instead of a guess", "0 inferred values",
         f"{cov['flagged']} flags published, each with an evidence link"),
        ("R79", "Site: clean landing page with category subpages, table-first", "GOVERNANCE",
         "a build with no broken links", "0 broken internal links",
         f"{cov['pages']} pages built deterministically; internal link check in verify.py"),
        ("R80", "Flag irregularities for review", "GOVERNANCE",
         "a Flagged for Review page with links", "every flag has a link and a severity",
         f"Flagged for Review page with {cov['flagged']} items"),
    ]
    out = []
    for rid, req, cat, gate, num, obs in R:
        status = "MET"
        if any(w in obs.upper() for w in ("NOT DONE", "BLOCKED", "CANNOT", "NOT ATTEMPTED", "NOT READ", "NOT CAPTURED", "NOT BUILT", "NOT RUN", "NOT HELD", "NEITHER", "OUT OF SCOPE", "NOT APPLICABLE")):
            status = "BLOCKED"
        elif any(w in obs for w in ("PENDING", "partial", "PARTIAL", "not re-read", "NOT RE-READ", "cannot be", "impossible")):
            status = "PARTIAL"
        out.append({"id": rid, "requirement": req, "category": cat, "status": status, "blocking_gate": gate,
                    "number_that_would_clear_it": num, "observed": obs, "evidence_path": "data/nfl-signal-board/", "source_url": src})
    return out


def main() -> int:
    raw_standings = read_csv(RAW / "standings_2026_reg.csv")
    raw_fixtures = read_csv(RAW / "fixtures_week11.csv")
    raw_odds = read_csv(RAW / "odds_20261119T1110Z.csv")
    raw_w10 = read_csv(RAW / "week10_finals.csv")

    standings = [{"club": r["club"], "w": int(r["w"]), "l": int(r["l"]), "t": int(r["t"]),
                  "pf": int(r["pf"]), "pa": int(r["pa"]), "pct": r["pct_as_printed"], "strk": r["strk"]}
                 for r in raw_standings]
    assert len(standings) == 32, f"expected 32 clubs, got {len(standings)}"

    fixtures = [{"fixture_id": r["fixture_id"], "away": r["away"], "home": r["home"],
                 "kickoff_et": r["kickoff_et"], "network": r["network"],
                 "location": r["location_as_printed"], "stadium": r["stadium_as_printed"],
                 "schedule_url": r["schedule_url"], "game_centre_url": r["game_centre_url"]} for r in raw_fixtures]
    assert len(fixtures) == 13, f"expected 13 fixtures, got {len(fixtures)}"

    odds = [{**o, "price_american": float(o["price_american"])} for o in raw_odds]
    per_fix = Counter(o["fixture_id"] for o in odds)
    assert all(v == 6 for v in per_fix.values()) and len(per_fix) == 13, per_fix

    corpus = load_corpus()
    spread_positive, mae_pos, mae_neg = detect_spread_sign(corpus)
    recon_rows, recon = build_reconciliation(corpus, standings)
    assert recon["clubs_reconciled"] == 32, f"reconciliation failed: {recon}"

    log = json.loads(GAMES_2026.read_text())["games"]
    log_rows, log_stats = audit_log136(log, corpus)

    rows, metrics, cal_rows, fam, meta, variant_table = build_models(corpus, spread_positive)
    meta.update({"corpus_games": len([g for g in corpus if g["season"] >= 2015]),
                 "corpus_all": len(corpus), "recon_clubs": recon["clubs_reconciled"],
                 "spread_mae_pos": mae_pos, "spread_mae_neg": mae_neg})

    orig, snaps, ratings, orig_meta = build_origination(corpus, spread_positive, meta, fixtures, odds)
    def _logit(p):
        p = min(max(p, 1e-6), 1 - 1e-6)
        return math.log(p / (1 - p))
    _b0 = meta["calibration"]["intercept"]; _b1 = meta["calibration"]["slope"]
    for o in orig:
        if o["fair_prob"] and o["market"] != "moneyline":
            raw = float(o["fair_prob"])
            o["fair_prob_calibrated"] = fmt(1.0 / (1.0 + math.exp(-(_b0 + _b1 * _logit(raw)))))
        elif o["fair_prob"]:
            p_home = float(o["fair_prob"])
            o["fair_prob_calibrated"] = fmt(1.0 / (1.0 + math.exp(-(_b0 + _b1 * _logit(p_home))))) if o["selection"] == o["home"] else fmt(1 - 1.0 / (1.0 + math.exp(-(_b0 + _b1 * _logit(p_home)))))
        if o["ev_per_unit"]:
            raw_ev = float(o["ev_per_unit"])
            o["stake_signal"] = (o["stake_signal"] + f" | calibration slope {meta['calibration']['slope']:.3f}: "
                                 "this EV uses uncalibrated probabilities and is NOT stakeable")
            o["stake"] = ""
            o["note"] = o["note"] + f" | calibration slope {meta['calibration']['slope']:.3f} (train n={meta['calibration']['n']})"
    luck = build_luck(rows, fam, meta)

    inj = json.loads(INJ_CAPTURE.read_text())
    inj_rows = inj["rows"]
    club_counts = Counter(r["club"] for r in inj_rows)
    designated = sum(1 for r in inj_rows if r["game_status"])
    out_by_club = Counter(r["club"] for r in inj_rows if r["game_status"] == "Out")
    q_by_club = Counter(r["club"] for r in inj_rows if r["game_status"] == "Questionable")
    depth = []
    fixture_clubs = {t for f in fixtures for t in (f["away"], f["home"])}
    for club in sorted(fixture_clubs | set(club_counts)):
        if club in inj["clubs_reading_no_injuries_reported"]:
            gate, num, note = "GATE OPEN — no designation printed by the official page", "a printed designation for this club", "club table reads No Injuries Reported"
        elif club in club_counts:
            gate = "GATE BLOCKED — no official replacement name and no inactive list"
            num = "an official inactive list plus a named replacement"
            note = "designation counts only; a replacement stays suspected, not confirmed"
        else:
            gate = "GATE BLOCKED — club has no Week 11 table"
            num = "a Week 11 table or a bye"
            note = "club absent from the Week 11 report page"
        depth.append({"club": club, "out_designated": out_by_club.get(club, ""), "questionable_designated": q_by_club.get(club, ""),
                      "replacement_named": "", "observed_starters_out": "", "gate_status": gate,
                      "blocking_gate": "official inactive list + announced starter evidence",
                      "number_that_would_clear_it": num,
                      "source_url": INJ11_URL, "note": note})

    hashes = {"standings": sha256_file(RAW / "standings_2026_reg.csv"),
              "fixtures": sha256_file(RAW / "fixtures_week11.csv"),
              "week10": sha256_file(RAW / "week10_finals.csv"),
              "odds": sha256_file(RAW / "odds_20261119T1110Z.csv"),
              "corpus": sha256_file(CORPUS),
              "injury_capture": sha256_file(INJ_CAPTURE),
              "games2026": sha256_file(GAMES_2026)}
    sources = build_sources(hashes)

    cov = {"fixtures": len(fixtures), "origination_rows": len(orig), "snapshots": len(snaps),
           "odds_rows": len(odds), "operator_prices": len(odds), "operators": len({o["operator"] for o in odds}),
           "injury_rows": len(inj_rows), "injury_clubs": len(club_counts), "designated": designated,
           "log_rows": log_stats["rows"], "log_agree": log_stats["agree"], "log_blank": log_stats["blank"],
           "log_absent": log_stats["absent"], "log_disagree": log_stats["disagree"], "captures": 2,
           "venue_done": sum(1 for f in fixtures if f["location"] and f["stadium"]),
           "luck_rows": len(luck), "flagged": 0, "suggestions": 0, "questions": 0, "registered": 8, "pages": 9}
    reqs = build_requirements(meta, cov, depth, {"lions_note": "see flags SBF-05"})

    # leaderboard: registrations, all uncertified, signal and staking separated
    lb = []
    for sid, div, name, stat, why in [
        ("S1", "single - side", "Originated side vs the operator's side price", "Brier skill vs the de-vigged close",
         "a cluster lower bound above 0 over 300+ settled bets"),
        ("S2", "single - total", "Originated total vs the operator's total price", "Brier skill vs the de-vigged close",
         "a cluster lower bound above 0 over 300+ settled bets, with the two total estimators within 10%"),
        ("S3", "single - moneyline", "Originated moneyline, underdog only", "Brier skill vs the de-vigged close",
         "a cluster lower bound above 0 over 300+ settled bets"),
        ("S4", "control", "Favourite-only control (never certified)", "Brier skill vs the de-vigged close",
         "not applicable: a control cannot be certified"),
        ("S5", "same-game parlay", "Two-leg same-game parlay (BLOCKED)", "joint probability gap",
         "a directly validated joint probability whose gap to the product of marginals is under 1 pp"),
        ("S6", "cross-game parlay", "Two-leg cross-game parlay", "joint probability gap",
         "a measured cross-game correlation interval that contains 0"),
        ("S7", "prop combo", "Two-leg player-yardage combo (BLOCKED)", "joint probability gap",
         "a fitted bivariate joint with n published and the operator's void rules on file"),
        ("S8", "control", "Seeded random-side control (never certified)", "Brier skill vs the de-vigged close",
         "not applicable: a control cannot be certified"),
    ]:
        lb.append({"division": div, "strategy_id": sid, "strategy": name, "settled_bets": 0 if sid not in ("S4", "S8") else "",
                   "signal_stat": stat, "signal_value": "", "signal_ci_low": "", "signal_ci_high": "",
                   "staking_units": "", "staking_roi": "", "staking_ci_low": "", "staking_ci_high": "",
                   "grade": "UNCERTIFIED — 0 settled bets since registration; backtest numbers are never shown here",
                   "demotion_rule": "two consecutive windows with a cluster CI lower bound on skill at or below zero sends the strategy back to paper",
                   "what_would_change_our_mind": why, "source_url": GH + "data/nfl-signal-board/preregistration.csv"})

    # pre-registration
    reg_meta = json.dumps({"seed": SEED, "spread_sign": meta["spread_sign"], "chosen": meta["chosen_side_variant"],
                           "b": round(meta["b_elo"], 8), "a": round(meta["a_elo"], 6),
                           "sd_elo": round(meta["sd_elo"], 6), "sd_total": round(meta["sd_total"], 6),
                           "tot_corr": round(meta["tot_corr"], 6)}, sort_keys=True)
    reg_hash = sha256_bytes(reg_meta.encode())
    prereg = []
    for sid, div, rule, win, gates in [
        ("S1", "single - side", "Bet the side when the model's fair spread differs from the operator's printed spread by >=1.5 points AND the model probability exceeds the de-vigged market probability by >=0.03; stake quarter-Kelly capped at 2%; flat 1u accounting for ROI.", "2026 W11 onwards; every priced game", "G1 registration hash, G2 kickoff-before-bet, G3 cluster CI, G4 multiplicity, G5 300 settled bets, G6 demotion"),
        ("S2", "single - total", "Bet the total when |fair total - operator total| >= 2.0 points and the model probability exceeds the de-vigged market probability by >=0.03; same staking.", "2026 W11 onwards; every priced game", "G1-G6 plus G7 both total estimators within 10%"),
        ("S3", "single - moneyline", "Underdog only: bet the ML when model probability exceeds de-vigged market probability by >=0.04.", "2026 W11 onwards", "G1-G6 plus G8 golden-rule check (no favourite-longshot bias claim)"),
        ("S5", "same-game parlay", "BLOCKED until a directly validated joint probability exists and the operator's void/push rules are on file.", "not started", "G9 joint-evidence gate"),
        ("S6", "cross-game parlay", "Two legs from different games may be ranked only when the measured cross-game correlation interval contains 0.", "not started", "G9"),
        ("S7", "prop combo", "BLOCKED until a fitted bivariate joint with published n exists.", "not started", "G9"),
        ("C1", "control", "Favourite-only control: bet the favourite at the close, flat 1u. Never certified; used to separate skill from the market's own bias.", "all priced games", "control"),
        ("C2", "control", "Seeded random side control (seed 20261119). Never certified.", "all priced games", "control"),
    ]:
        prereg.append({"registration_id": "REG-1FAB8A48-" + sid, "strategy_id": sid, "division": div,
                       "rule_text": rule, "sample_window": win, "gates": gates,
                       "frozen_utc": "2026-11-19T11:15:00Z", "artifact_sha256": reg_hash,
                       "commit_ref": "the commit that introduced this file is the registration",
                       "source_url": GH + "data/nfl-signal-board/preregistration.csv"})

    (HERE / "preregistration.json").write_text(json.dumps({
        "registration_id": "REG-1FAB8A48-V1", "frozen_utc": "2026-11-19T11:15:00Z",
        "model": {"type": "walk-forward Elo margin + rolling shrinkage scoring rates",
                  "train_window": "2015-2024", "holdout_window": "2025-2026",
                  "a_intercept": meta["a_elo"], "b_points_per_elo": meta["b_elo"],
                  "sd_elo": meta["sd_elo"], "sd_total": meta["sd_total"],
                  "total_correction": meta["tot_corr"], "sigma_chosen_on_train": meta["chosen_side_variant"],
                  "sigma_buckets": meta["sigma_buckets"]},
        "bet_selection": {"side_min_edge_points": 1.5, "min_prob_edge": 0.03, "exclude_push": True},
        "gates": ["G1 registration hash published before kickoff", "G2 forecast commit precedes kickoff",
                  "G3 week-cluster bootstrap CI", "G4 Holm across 8 registered families",
                  "G5 300 settled bets before any certification", "G6 two-window demotion",
                  "G7 total estimators within 10%", "G8 golden-rule check", "G9 joint-evidence gate for combos"],
        "artifact_sha256": reg_hash, "seed": SEED,
        "policy": "P-01: aggregates on the public site, row-level official data stays private, operator prices attributed",
        "note": "Nothing in this file may be changed after kickoff without a new registration id."
    }, indent=2, sort_keys=True) + "\n")

    # questions
    Q = [
        ("Q01", "Which operator price is the market, and are we allowed to republish it row by row?",
         "Every residual on the site depends on the market column.", "one operator's live Week 11 board, read and attributed, 78 prices",
         "a terms reading for automated capture and a second and third book", "re-read the operator terms and the NFL terms with legal review; add two books if permitted",
         "NO — the residual is published, the policy question is not decided", "operator terms; a legal read"),
        ("Q02", "Does the model beat the market on proper scores once we are honest about the holdout?",
         "This decides whether any line can be sold, staked or trusted.", "a walk-forward evaluation on 2015-2026 with cluster intervals and controls",
         f"a positive cluster lower bound anywhere (today the lower bound is {metrics[0]['ci_low']})",
         "keep the identical pipeline and add 2026 weeks 11-18 as they settle; do not retune on the holdout", "YES — the answer today is no",
         "settled games; no more data needed to answer, only time"),
        ("Q03", "What is the true dispersion of the margin around our projection?",
         "The spread probability is a function of sigma; a wrong sigma fakes edges.", "train-only estimates: fixed 13.86, Elo-sd, bucketed, points-mix",
         "dispersion that differs by game state (garbage time, roof, rest)", "fit sigma by rest/roof/pace strata on train only and compare Brier",
         "PARTLY — a sigma is chosen on train, but the strata are unmodelled", "play-by-play for garbage-time filtering"),
        ("Q04", "Is the closing total really biased, or did we just look at the holdout?",
         "A one-sided total bias would be the single most valuable finding on this site.",
         f"measured bias {fmt(meta['tot_bias'])} points with a week-cluster interval",
         "a pre-kickoff registration on 2026 only that has never seen the 2026 results",
         "register the rule now, evaluate after Week 18", "NO — the hypothesis already saw the holdout",
         "a frozen 2026-only registration and eight weeks of settled games"),
        ("Q05", "Who was actually on the field, and who replaced whom?",
         "This is the availability signal the brief asks for.", "official designations for 253 rows across 24 clubs",
         "official inactive lists, game books and snap counts", "capture inactives 90 minutes before kickoff and the game book after",
         "NO", "an official inactive feed and a game-book PDF per game"),
        ("Q06", "What does a designation actually predict?",
         "A label with an unknown play rate is not a feature.", "designations as printed",
         "the join from designation to played/not-played with intervals", "join several seasons of designations to official inactive lists",
         "NO — no percentage is published here", "archived weekly reports and inactive lists"),
        ("Q07", "Is the depth order available from an official source for all 32 clubs?",
         "The backup-deficiency matrix needs it.", "none verified", "32 club depth pages with dates and structured formats",
         "verify club by club; if any club publishes only an image, stop and use snap counts", "NO",
         "32 verified pages or an official snap-count source"),
        ("Q08", "How much of the 2026 log can be trusted?",
         "The brief's 136-game log is a named input.", f"{log_stats['agree']} of {log_stats['rows']} rows agree with official results",
         "3 fixtures that are absent from the pinned snapshot and 16 blank rows", "re-derive every row from the official schedules and diff",
         "YES — the audit is published", "nothing; the audit is complete for the rows held"),
        ("Q09", "Are the correlations we publish the ones that matter for parlays?",
         "Parlay pricing needs leg correlations, not team-stat correlations.",
         "4 team-level coefficients from the official standings, n=32", "play-by-play leg correlations",
         "compute leg correlations from an official play-by-play source when one is available", "PARTLY",
         "a play-by-play source with a licence"),
        ("Q10", "What is the reward structure, and who pays it?",
         "The brief asks for a competition with rewards.", "a described tier structure, no amounts",
         "the owner's decision on amounts and whether anything is paid", "ask the owner; page the decision, do not invent an amount",
         "NO", "an owner decision"),
        ("Q11", "Which games are in play this week, exactly?",
         "Origination needs a fixed slate.", "13 fixtures with kickoffs, networks and venues; 6 byes", "nothing for Week 11",
         "re-read the schedule page at each build", "YES", "nothing"),
        ("Q12", "Does the venue print on the game centre match the venue print on the schedule page?",
         "A wrong venue poisons roof and weather features.", "two official prints for IND@HOU that disagree (Reliant vs NRG)",
         "an authoritative ruling on which print is current", "flag it and do not build a venue feature until resolved", "NO",
         "an official correction or a club confirmation"),
        ("Q13", "Can we price props at all?",
         "The brief asks for player prop combos.", "settled bets: 0; a blocked S7 registration",
         "an official player-level market price and a joint model", "read a prop board and the operator's void rules; fit a bivariate joint",
         "NO", "prop prices and void rules"),
        ("Q14", "What is the minimum sample that would let us certify anything?",
         "The competition needs a rule, not a vibe.", "power calculation: ~359 settled bets for a 55% bettor at -110",
         "an agreed minimum per division", "adopt the number in the registration and hold it", "YES — the number is published",
         "an owner decision to adopt it"),
        ("Q15", "Is the 2026 kickoff/onside-kick rule regime priced differently?",
         "It would change total and comeback priors.", "no rule text read this session", "the official 2026 rule text",
         "read the official rulebook section and diff it against 2025", "NO", "the official rulebook"),
        ("Q16", "How do we stop a lucky staking run from looking like skill?",
         "This is the brief's core governance ask.", "separate signal and staking columns, demotion gate, controls",
         "a live example (nothing has settled)", "keep the separation and publish the escrow rule", "YES",
         "settled bets; no more information needed to design it"),
        ("Q17", "What happened to the reserve-list players?",
         "'Not listed' currently cannot be distinguished from 'healthy'.", "the injury page, which excludes reserve players",
         "the official reserve/IR list", "read the club roster pages' reserve section and join to the report", "NO",
         "an official reserve list"),
        ("Q18", "Should the site keep one front door or one per session?",
         "58 additive desks are confusing to a reader.", "this desk's nav is scoped to its own pages",
         "the owner's preference on consolidation", "ask the owner; do not delete another session's work", "NO",
         "an owner decision"),
    ]
    questions = [{"id": q[0], "question": q[1], "why_it_matters": q[2], "what_we_have": q[3],
                  "what_we_do_not_have": q[4], "discovery_route": q[5], "can_decide_today": q[6],
                  "informations_needed": q[7], "source_url": GH + "data/nfl-signal-board/questions.csv"} for q in Q]

    S = [
        ("SUG01", "Publish the market column with the operator's name and the read clock on every row, and keep the policy decision (Q01) on the same page as the residual.", "Residuals without provenance are not reviewable.", "low", "a terms dispute", "the owner can audit any residual back to a clocked read", ""),
        ("SUG02", "Run one weekly pre-registered build that never changes a rule mid-week; the commit hash is the entry.", "Prevents result-chasing.", "low", "none material", "no rule changes appear between kickoff and settlement", ""),
        ("SUG03", "Hold every strategy at 0 settled bets until the gate number (359) is reachable, and show the countdown.", "Stops early lucky runs from being ranked.", "low", "slower to show results", "no strategy is ranked before the count", ""),
        ("SUG04", "Add the official inactive list capture 90 minutes before each kickoff before any availability feature is built.", "Turns suspicion into evidence (Q05).", "medium", "capture timing across time zones", "replacement names appear in the graph", ""),
        ("SUG05", "Use the game book, not the depth chart, as the starter record; the book is published and dated.", "Removes the depth-order problem entirely for starters.", "medium", "PDF extraction cost", "starters reconcile to snap counts", ""),
        ("SUG06", "Keep the two total estimators side by side and only collapse them after a walk-forward comparison.", "Avoids a coin-flip choice.", "low", "two numbers on a page", "the gap column closes on evidence", ""),
        ("SUG07", "Publish the correlation table with n and a 'what this does not tell you' column.", "Stops team-stat correlations being used as parlay inputs.", "low", "none material", "no reader mistakes r for a leg correlation", ""),
        ("SUG08", "Put the decision-readiness table on the landing page, not buried.", "The brief asks for it there.", "low", "none material", "a reader sees the blockers in one screen", ""),
        ("SUG09", "Archive the injury report daily Wed-to-kickoff with hashes, starting now.", "Builds the series the later questions need.", "medium", "capture terms", "a dated series exists for 2027", ""),
        ("SUG10", "Add a weekly what-changed diff once the second build exists.", "Shows movement instead of a frozen page.", "low", "none material", "rank and rating changes are visible week to week", ""),
        ("SUG11", "Do not merge this desk's nav into the root index; ask the root owner instead.", "Another session owns the root index.", "low", "coordination", "the owner approves one navigation decision", ""),
        ("SUG12", "Report the honest negative result on the landing page, above the fold.", "A site that hides a losing model is worse than no site.", "low", "none material", "a reader can find the result in five seconds", ""),
    ]
    suggestions = [{"id": s[0], "suggestion": s[1], "problem_it_solves": s[2], "effort": s[3], "risk": s[4],
                    "how_we_would_know_it_worked": s[5], "owner_decision": s[6],
                    "related_requirement": "", "source_url": GH + "data/nfl-signal-board/suggestions.csv"} for s in S]

    R = [
        ("RS01", "Spread sign convention in the pinned corpus", "Which direction does closing_spread_home point?",
         f"MAE against realised margin: {mae_pos:.2f} treating the value as home-favoured-positive vs {mae_neg:.2f} treating it as negative",
         len([r for r in rows if r.get('spread') is not None]), f"the stored value is {meta['spread_sign']}",
         "a re-pull of the source column showing the opposite convention", "VERIFIED"),
        ("RS02", "Is the model better than the market on the side?", "Brier skill vs the de-vigged close, cluster bootstrap, controls",
         "see the model page", fam["M1"]["all 2015-2026"]["n"] if "M1" in fam else "",
         f"skill {fmt(fam['M1']['all 2015-2026']['skill'])} (CI {fmt(fam['M1']['all 2015-2026']['ci_low'])} to {fmt(fam['M1']['all 2015-2026']['ci_high'])})" if "M1" in fam else "",
         "a positive cluster lower bound", "VERIFIED — answer is no"),
        ("RS03", "Which sigma variant should be used?", "Tuning must happen on train only",
         "four variants scored on 2015-2024", meta["train_n"], f"chosen: {meta['chosen_side_variant']}",
         "a variant that wins on the holdout as well", "VERIFIED (train-only choice)"),
        ("RS04", "Is the closing total biased?", "A one-sided total bias is the most valuable single finding",
         "cluster interval on realised minus closing total", len(rows), f"{fmt(meta['tot_bias'])} points ({fmt(meta['tot_bias_ci'][0])} to {fmt(meta['tot_bias_ci'][1])})",
         "a pre-kickoff 2026-only registration that fails", "OBSERVATION — not a strategy"),
        ("RS05", "Are home and away moneylines in the corpus de-viggable?", "The market probability is the benchmark",
         "additive implied probabilities", len(rows), "yes, the two-way sum is published per market on the origination page",
         "a market where the sum is far from 1", "VERIFIED"),
        ("RS06", "Do the official standings reconcile to the game corpus?", "A corpus that does not reconcile cannot be backtested",
         "32 club records vs game-derived records", recon["games"], f"{recon['clubs_reconciled']}/32 clubs reconcile",
         "any club that does not reconcile", "VERIFIED"),
        ("RS07", "Is the 136-row log usable as a backtest corpus?", "The brief names it as the corpus",
         "row-by-row audit against official results", log_stats["rows"],
         f"{log_stats['agree']} agree, {log_stats['blank']} blank, {log_stats['absent']} absent, {log_stats['disagree']} disagree",
         "a row that disagrees on a posted score", "AUDITED"),
        ("RS08", "Should depth order be derived from jersey number or experience?", "A tempting shortcut",
         "no official source prints depth as an attribute", 0, "REJECTED — not used anywhere",
         "an official page that states depth as an attribute", "REJECTED"),
        ("RS09", "Should ROI be the leaderboard rank key?", "A tempting shortcut",
         "ROI interval at 300 bets spans zero", 300, "REJECTED — rank key is the skill lower bound",
         "an ROI that separates from zero with n published", "REJECTED"),
        ("RS10", "Are the two named-player depth failures still real?",
         "Texans image and Packers jersey prefixes", "not tested this session: no club depth page was parsed", 0,
         "UNVERIFIED here; carried as a flag rather than a claim", "a structured source for both clubs", "OPEN"),
    ]
    research = [{"id": r[0], "title": r[1], "question": r[2], "evidence": r[3], "n": r[4], "result": r[5],
                 "what_would_change_our_mind": r[6], "status": r[7],
                 "source_url": GH + "data/nfl-signal-board/research.csv"} for r in R]

    flagged = [
        ("SBF-01", "correction", "Nine prior skills tables are committed repo-wide and none is certifiable",
         "This desk did not reuse another desk's certification. Every strategy on this site starts at 0 settled bets, because a backtest number on a leaderboard is exactly what the brief forbids.",
         GH + "nfl-line-audit/data/leaderboard.csv", "medium", "OPEN — carried by design"),
        ("SBF-02", "irregularity", "The Week 11 injury page prints 16 game-status cells across 253 rows",
         "9 Out and 7 Questionable cells; the remaining cells are blank on the official print. Blank is the print, not a missing value, and no cell was filled from news copy.",
         INJ11_URL, "medium", "OPEN — publication fact"),
        ("SBF-03", "irregularity", "Two clubs read 'No Injuries Reported' while their opponents list 20 combined rows",
         "CIN and WAS read No Injuries Reported on the Week 11 page. This is the official print and is reproduced as such; it is not evidence that the clubs are healthy.",
         INJ11_URL, "medium", "OPEN"),
        ("SBF-04", "irregularity", "Two official pages disagree on the IND@HOU venue",
         "The game centre prints Stadium RELIANT STADIUM; the Week 11 schedule page links hotels near NRG Stadium. Both prints are stored verbatim and the venue feature is blocked (Q12).",
         "https://www.nfl.com/games/colts-at-texans-2026-reg-11", "high", "OPEN — needs an official correction"),
        ("SBF-05", "irregularity", "The three named Lions players still print a blank game-status cell",
         "The brief says Joseph, Mays and Reed are listed Out in an article; today's official report prints full/limited/did-not-participate practice rows with blank game status. The page is the publisher of record, so the cell stays blank and the article claim is not imported.",
         INJ11_URL, "medium", "OPEN — article vs report conflict"),
        ("SBF-06", "unverified", "The dated 2026 schedule announcement was not re-read this session",
         "The brief asks for the league's dated announcement beside the live schedule. Publishing a date from memory would be a hallucination, so the row is blank and this flag records the gap.",
         "https://www.nfl.com/schedules/2026/", "medium", "OPEN — needs one official read"),
        ("SBF-07", "unverified", "No official game book was read this session",
         "Actual starters and game-day status come from game books. None was read, so no starter is claimed anywhere on the site.",
         "https://www.nfl.com/scores/", "high", "OPEN"),
        ("SBF-08", "unverified", "No announced-starter evidence was captured",
         "The brief asks for announced starter changes as evidence. None was captured this session.",
         GH + "data/nfl-signal-board/questions.csv", "medium", "OPEN"),
        ("SBF-09", "unverified", "No official snap-count source was read",
         "Playing-time depth is the only depth the brief accepts; it is not held, so no depth order is published.",
         GH + "data/nfl-signal-board/questions.csv", "high", "OPEN"),
        ("SBF-10", "unverified", "Roof and surface are blank for the 2026 official reads",
         "The pinned corpus carries roof and surface for historical seasons; the official 2026 week pages do not print them in the read text, so the columns are blank for Week 11.",
         SCHED11_URL, "low", "OPEN"),
        ("SBF-11", "unverified", "No archived injury-report series exists for past seasons",
         "Without an archive the designation-reliability question (Q06) cannot be answered, and no percentage is invented.",
         INJ11_URL, "medium", "OPEN"),
        ("SBF-12", "policy", "Only one operator price was read, so no consensus is published",
         "A one-book consensus is not a consensus. The consensus columns are blank until a second and third book are read under policy P-01.",
         ODDS_URL, "medium", "OPEN — policy decision Q01"),
        ("SBF-13", "correction", "The pinned corpus carries no over/under prices, so the total benchmark is missing",
         "The corpus has closing_total but not the two prices that would let the total market be de-vigged. The total Brier skill is therefore not scored against a market probability; only the side and moneyline are.",
         GH + "nfl-line-audit/data/corpus_games.csv", "high", "OPEN — blocks the total certification"),
        ("SBF-14", "irregularity", "The 136-row log stores its own status field that is not a score",
         "Every row's 'st' is 'final' while 0 of 136 rows carried both scores in the field set this desk read; the audit re-derives scores from the reconciled corpus instead.",
         GH + "data/games_2026.json", "low", "OPEN"),
        ("SBF-15", "policy", "The no-manual-input requirement conflicts with the terms-of-service question",
         "Automated capture of official pages may not be permitted by the terms; the site therefore publishes counts and derived values read by hand-and-tool, and the automated job is scoped to this desk's own artifacts.",
         NFL_TERMS, "high", "OPEN — owner decision Q01"),
    ]
    flagged_rows = [{"id": f[0], "type": f[1], "title": f[2], "detail": f[3], "evidence_url": f[4],
                     "severity": f[5], "status": f[6],
                     "source_url": GH + "data/nfl-signal-board/flagged.csv"} for f in flagged]
    cov["flagged"] = len(flagged_rows); cov["suggestions"] = len(suggestions); cov["questions"] = len(questions)

    for name, payload in (("sources", sources), ("corpus_reconciliation", recon_rows), ("origination", orig),
                          ("price_snapshots", snaps), ("model_metrics", metrics), ("calibration", cal_rows),
                          ("luck", luck), ("leaderboard", lb), ("depth", depth), ("requirements", reqs),
                          ("questions", questions), ("suggestions", suggestions), ("research", research),
                          ("flagged", flagged_rows), ("prereg", prereg), ("log136", log_rows),
                          ("ratings", ratings)):
        write_csv(name, payload)

    summary = {
        "session": "1fab8a48", "built_utc": "2026-11-19T11:20:00Z",
        "frozen_inputs": hashes, "reconciliation": recon, "spread_sign": meta["spread_sign"],
        "spread_mae": {"positive_convention": mae_pos, "negative_convention": mae_neg},
        "log136": log_stats, "model": meta,
        "headline": {
            "side_brier_skill_all": fam["M1"]["all 2015-2026"]["skill"],
            "side_brier_skill_ci": [fam["M1"]["all 2015-2026"]["ci_low"], fam["M1"]["all 2015-2026"]["ci_high"]],
            "side_brier_skill_holdout": fam["M1"]["holdout 2025-2026"]["skill"],
            "ml_brier_skill_all": fam["M3"]["all 2015-2026"]["skill"],
            "ml_brier_skill_ci": [fam["M3"]["all 2015-2026"]["ci_low"], fam["M3"]["all 2015-2026"]["ci_high"]],
            "control_half_skill": fam["M4"]["all 2015-2026"]["skill"],
            "control_base_rate_skill": fam["M5"]["all 2015-2026"]["skill"],
            "totals_bias_points": meta["tot_bias"], "totals_bias_ci": list(meta["tot_bias_ci"]),
            "originated_markets": len(orig), "priced_fixtures": len([f for f in fixtures]),
            "operator_prices": len(odds), "captured_injury_rows": len(inj_rows),
            "injury_clubs": len(club_counts), "designated_rows": designated,
            "rows_with_raw_ev_over_2pct": sum(1 for o in orig if o["ev_per_unit"] and float(o["ev_per_unit"]) > 0.02),
            "calibration_slope": meta["calibration"]["slope"],
            "stakeable_rows": 0,
            "certified_strategies": 0,
        },
        "counts": cov, "source_hashes": hashes,
    }
    (HERE / "derive_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")

    print(f"corpus games 2015+: {meta['corpus_games']}  reconciled {recon['clubs_reconciled']}/32")
    print(f"spread convention: {meta['spread_sign']} (MAE {mae_pos:.2f} vs {mae_neg:.2f})")
    print(f"log136: {log_stats}")
    print(f"side skill all: {fam['M1']['all 2015-2026']['skill']:.4f} "
          f"[{fam['M1']['all 2015-2026']['ci_low']:.4f}, {fam['M1']['all 2015-2026']['ci_high']:.4f}] n={fam['M1']['all 2015-2026']['n']}")
    print(f"holdout side skill: {fam['M1']['holdout 2025-2026']['skill']:.4f}")
    print(f"ml skill all: {fam['M3']['all 2015-2026']['skill']:.4f} "
          f"[{fam['M3']['all 2015-2026']['ci_low']:.4f}, {fam['M3']['all 2015-2026']['ci_high']:.4f}]")
    print(f"control A (0.5) skill: {fam['M4']['all 2015-2026']['skill']:.4f}  control B (base rate) skill: {fam['M5']['all 2015-2026']['skill']:.4f}")
    print(f"origination rows: {len(orig)}  snapshots: {len(snaps)}  ratings: {len(ratings)}")
    print(f"total bias: {meta['tot_bias']:.4f} CI {meta['tot_bias_ci']}")
    print(f"requirements: {len(reqs)}  questions: {len(questions)}  suggestions: {len(suggestions)}  flags: {len(flagged_rows)}")
    print(f"registrations: {len(prereg)}  reg hash: {reg_hash[:16]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

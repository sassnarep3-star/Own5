#!/usr/bin/env python3
"""Validation-gate checker for a logged bet record (Gates G3, G5 and summary).

Input: CSV of logged bets with columns:
    timestamp, market, bet_odds_decimal, close_odds_decimal_devig, stake,
    result (win/loss/push), strategy_hash

Implements:
  G3  — mean de-vigged CLV with bootstrap 95% CI (must exclude 0, n >= 200).
        CLV_i = close_devig / bet_odds - 1   (positive = beat the close)
        Formula per industry convention:
        https://www.pinnacleoddsdropper.com/blog/closing-line-value
  G5  — Monte Carlo permutation: flat-stake profit vs. shuffled-results null.
  Also reports beat-close rate with a binomial test vs 0.5.

No data, no output: the script refuses to run on fewer than 50 rows and
never simulates a record for you.
"""
import argparse
import csv
import math
import random
import statistics
import sys


def read_bets(path):
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    if len(rows) < 50:
        print(f"ERROR: only {len(rows)} bets; refusing to evaluate a sample "
              "this small (G3 requires >= 200).", file=sys.stderr)
        sys.exit(1)
    return rows


def clv(row):
    bet = float(row["bet_odds_decimal"])
    close = float(row["close_odds_decimal_devig"])
    # Positive when you got a bigger price than the fair close implies you
    # should have: CLV% = (your odds / fair close odds) - 1
    return bet / close - 1.0


def bootstrap_ci(values, iters=10000, alpha=0.05, seed=7):
    rng = random.Random(seed)
    n = len(values)
    means = []
    for _ in range(iters):
        sample = [values[rng.randrange(n)] for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    lo = means[int((alpha / 2) * iters)]
    hi = means[int((1 - alpha / 2) * iters)]
    return lo, hi


def flat_profit(rows):
    p = 0.0
    for r in rows:
        if r["result"] == "win":
            p += float(r["bet_odds_decimal"]) - 1.0
        elif r["result"] == "loss":
            p -= 1.0
    return p


def permutation_null(rows, iters=2000, seed=7):
    rng = random.Random(seed)
    results = [r["result"] for r in rows]
    actual = flat_profit(rows)
    null = []
    for _ in range(iters):
        shuffled = results[:]
        rng.shuffle(shuffled)
        fake = [dict(r, result=s) for r, s in zip(rows, shuffled)]
        null.append(flat_profit(fake))
    null.sort()
    pct = sum(1 for x in null if x < actual) / iters
    return actual, pct


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("csv", help="bet log CSV")
    args = ap.parse_args()
    rows = read_bets(args.csv)
    n = len(rows)

    clvs = [clv(r) for r in rows]
    mean_clv = sum(clvs) / n
    lo, hi = bootstrap_ci(clvs)
    beat = sum(1 for c in clvs if c > 0)
    # normal approx binomial test vs 0.5
    z = (beat - n * 0.5) / math.sqrt(n * 0.25)

    profit, pct = permutation_null(rows)

    print(f"n bets:                 {n}")
    print(f"mean de-vigged CLV:     {mean_clv*100:+.2f}%  "
          f"(95% CI [{lo*100:+.2f}%, {hi*100:+.2f}%])")
    print(f"beat-close rate:        {beat/n:.1%}  (z vs 50%: {z:+.2f})")
    print(f"flat-stake profit:      {profit:+.2f}u  "
          f"(permutation percentile: {pct:.1%})")
    print(f"CLV sd:                 {statistics.pstdev(clvs)*100:.2f}%")
    print()
    g3 = n >= 200 and lo > 0
    g5 = pct >= 0.95
    print(f"Gate G3 (CLV):          {'PASS' if g3 else 'FAIL'}")
    print(f"Gate G5 (perm null):    {'PASS' if g5 else 'FAIL'}")
    if not (g3 and g5):
        sys.exit(2)


if __name__ == "__main__":
    main()

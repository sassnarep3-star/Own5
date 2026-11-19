"""Correlations computed ONLY from officially sourced standings (n=32), n published per row."""
import csv, math, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "nfl-desk-2b6d55c1")


def mean(xs):
    return sum(xs) / len(xs)


def pearson(xs, ys):
    n = len(xs)
    mx, my = mean(xs), mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if dx == 0 or dy == 0:
        return 0.0
    return num / (n * dx * dy) if False else num / ((n - 1) * dx * dy) * (n - 1) / n


def pearson_r(xs, ys):
    n = len(xs)
    mx, my = mean(xs), mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
    if den == 0:
        return 0.0, n
    return num / den, n


def ci_r(r, n):
    """Fisher-z 95% CI for a correlation."""
    if n <= 3:
        return "", ""
    z = 0.5 * math.log((1 + r) / (1 - r))
    se = 1.0 / math.sqrt(n - 3)
    lo = math.tanh(z - 1.96 * se)
    hi = math.tanh(z + 1.96 * se)
    return round(lo, 4), round(hi, 4)


def main():
    teams = []
    with open(os.path.join(DATA, "standings.csv"), newline="") as f:
        for row in csv.DictReader(f):
            gp = int(row["games_played"])
            teams.append({
                "abbr": row["abbr"],
                "W": int(row["W"]),
                "L": int(row["L"]),
                "T": int(row["T"]),
                "PCT": float(row["PCT"]),
                "PF": int(row["PF"]),
                "PA": int(row["PA"]),
                "gp": gp,
            })
    n = len(teams)
    for t in teams:
        t["PF_G"] = t["PF"] / t["gp"]
        t["PA_G"] = t["PA"] / t["gp"]
        t["NET_G"] = t["NET_G"] = (t["PF"] - t["PA"]) / t["gp"]

    def col(name):
        return [t[name] for t in teams]

    pairs = [
        ("PF/G", "PCT", col("PF_G"), col("PCT")),
        ("PA/G", "PCT", col("PA_G"), col("PCT")),
        ("NET/G", "PCT", col("NET_G"), col("PCT")),
        ("PF/G", "PA/G", col("PF_G"), col("PA_G")),
        ("W", "PCT", col("W"), col("PCT")),
    ]

    out = os.path.join(DATA, "correlations.csv")
    fields = ["corr_id", "variable_x", "variable_y", "r", "n", "ci_low", "ci_high",
              "source_url", "method", "verification_status", "notes"]
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for i, (x, y, xs, ys) in enumerate(pairs, 1):
            r, nval = pearson_r(xs, ys)
            lo, hi = ci_r(r, nval)
            w.writerow({
                "corr_id": f"CZ-{i:02d}",
                "variable_x": x,
                "variable_y": y,
                "r": round(r, 4),
                "n": nval,
                "ci_low": lo,
                "ci_high": hi,
                "source_url": "https://www.nfl.com/standings/league/2026/REG",
                "method": "Pearson product-moment (official standings)",
                "verification_status": "computed_from_official",
                "notes": "Computed in-repo from officially sourced standings. n published per row.",
            })
    print("wrote", out, n, "teams")


if __name__ == "__main__":
    main()

"""Originate Week 11 NFL lines from official standings only.

Specification (not a fitted forecast):
  team offense  = PF / games_played   (official standings)
  team defense  = PA / games_played   (official standings)
  HFA           = 2.0 points          (prior assumption, flagged FZ-02; not fitted)
  logistic scale = 13.7 points        (NFL convention, flagged FZ-03)

  Home expected points = (home_off + away_def)/2 + HFA/2
  Away expected points = (away_off + home_def)/2 - HFA/2
  fair spread (home - away) = home_exp - away_exp   (+ = home favoured)
  fair total             = home_exp + away_exp
  home win probability   = logistic((home_exp - away_exp) / scale)

  Market line and difference columns are left BLANK + FLAGGED: no verified
  operator price source exists (price-data policy P-01, flagged FZ-04).
  Every row stores its probability + inputs + inputs hash.
"""
import csv, json, math, hashlib, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "nfl-desk-2b6d55c1")

HFA = 2.0
SCALE = 13.7


def logistic(x):
    return 1.0 / (1.0 + math.exp(-x))


def american_odds(p):
    """Fair moneyline (American) for a win probability p (home side)."""
    if p <= 0.0 or p >= 1.0:
        return ""
    if p >= 0.5:
        return round(-100.0 * p / (1.0 - p), 1)
    return round(100.0 * (1.0 - p) / p, 1)


def main():
    teams = {}
    with open(os.path.join(DATA, "standings.csv"), newline="") as f:
        for row in csv.DictReader(f):
            gp = int(row["games_played"])
            teams[row["abbr"]] = {
                "team": row["team"],
                "abbr": row["abbr"],
                "off": float(row["PF"]) / gp,
                "def": float(row["PA"]) / gp,
                "net": float(row["NET"]),
            }

    rows = []
    with open(os.path.join(DATA, "schedule_w11.csv"), newline="") as f:
        for row in csv.DictReader(f):
            if not row["game_id"].startswith("W11"):
                continue
            away = row["abbr_away"]
            home = row["abbr_home"]
            t_away = teams[away]
            t_home = teams[home]

            home_exp = (t_home["off"] + t_away["def"]) / 2.0 + HFA / 2.0
            away_exp = (t_away["off"] + t_home["def"]) / 2.0 - HFA / 2.0
            fair_spread = home_exp - away_exp
            fair_total = home_exp + away_exp
            p_home = logistic((home_exp - away_exp) / SCALE)

            inputs = {
                "home_off": round(t_home["off"], 4),
                "home_def": round(t_home["def"], 4),
                "away_off": round(t_away["off"], 4),
                "away_def": round(t_away["def"], 4),
                "hfa": HFA,
                "scale": SCALE,
                "home_exp": round(home_exp, 4),
                "away_exp": round(away_exp, 4),
            }
            inputs_sha = hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest()[:16]

            # Side market
            rows.append({
                "game_id": row["game_id"],
                "away": row["away"],
                "home": row["home"],
                "market": "side",
                "model_fair": round(fair_spread, 2),
                "market_line": "",
                "difference": "",
                "probability": round(p_home, 4),
                "inputs": json.dumps(inputs),
                "inputs_sha": inputs_sha,
                "source_url": row["source_url"],
                "verification_status": "computed_from_official",
                "notes": "Home team listed second. Positive model_fair = home favoured. Market blank by price-data policy.",
            })
            # Total market
            rows.append({
                "game_id": row["game_id"],
                "away": row["away"],
                "home": row["home"],
                "market": "total",
                "model_fair": round(fair_total, 1),
                "market_line": "",
                "difference": "",
                "probability": "",
                "inputs": json.dumps(inputs),
                "inputs_sha": inputs_sha,
                "source_url": row["source_url"],
                "verification_status": "computed_from_official",
                "notes": "Fair total from scoring rates. Market blank by price-data policy.",
            })
            # Moneyline market
            ml_home = american_odds(p_home)
            rows.append({
                "game_id": row["game_id"],
                "away": row["away"],
                "home": row["home"],
                "market": "moneyline",
                "model_fair": ml_home,
                "market_line": "",
                "difference": "",
                "probability": round(p_home, 4),
                "inputs": json.dumps(inputs),
                "inputs_sha": inputs_sha,
                "source_url": row["source_url"],
                "verification_status": "computed_from_official",
                "notes": "Fair moneyline (American, home side) derived from home win probability. Market blank by price-data policy.",
            })

    out = os.path.join(DATA, "origination.csv")
    fields = ["game_id", "away", "home", "market", "model_fair", "market_line",
              "difference", "probability", "inputs", "inputs_sha", "source_url",
              "verification_status", "notes"]
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print("wrote", out, len(rows), "rows")


if __name__ == "__main__":
    main()

# Executive summary — NFL line-origination desk (session 715e2cd4)

**Read 2026-11-19.** Every number below is either computed in-repo from an official nfl.com page or
left blank and flagged. Nothing is estimated from memory. The site is at
`https://sassnarep3-star.github.io/Own5/nfl-desk-715e2cd4/`.

## 1. What exists now

| Item | State |
|---|---|
| Own fair lines, Week 11 2026 | **13 fixtures × 3 markets = 39 originated markets**, in the required order side → total → moneyline |
| Market prices for those 39 markets | **0**. Blank and flagged (F-01); policy P-01 forbids scraping operator odds before their terms are read |
| Verified results corpus | **136 official finals** (weeks 1-9), plus **14** in the Week 10 holdout |
| Corpus integrity | **32 of 32 clubs reconcile exactly** to the official standings on W-L-T-PF-PA |
| Certifiable strategies | **0** |
| Validation gates | 1 passed (G0) · 1 partial (G2) · 4 failed (G1, G3, G4, G5) · 3 blocked (G6, G8, G9) · 1 not triggered (G7) |
| Requirements tracked against the brief | **66**, each with its blocking gate and the number that would clear it |
| Official sources read with clock times | **12** |
| Flags for review | **23**, of which 5 are critical (F-01, F-07, F-13, F-16, F-18) |

## 2. The three findings that matter

**2.1 Both total estimators lose to a league-average total.** On the Week 10 holdout, estimator A
(sum of fitted expected points) scored a MAE of 9.199 and estimator B (club-average combined total)
8.896, while a constant league-mean total scored 8.204 — skills of **−0.121** and **−0.084**. That is
a fourteen-game sample, so the magnitude is not trustworthy, but the sign is not ours. The desk
publishes both estimators, the gap column and the loss, rather than averaging the problem away.

**2.2 The side model's apparent edge is uninformative.** The side beats a constant home-margin
baseline by 21.96% MAE (9.811 vs 12.571), but 14 observations produce a 95% interval of 5.44 to
14.18 points. Meanwhile the frozen model's home-field term is **−0.50 points**, because that is the
mean home margin in the official week 1-9 results (n=136). A negative HFA is not a mistake in the
code; it is what the official finals say, and it is raised as question Q04 rather than smoothed to a
textbook value.

**2.3 The sample requirement dwarfs everything available.** To separate a 55% bettor from the
52.4% break-even rate with 80% power takes about **5,773 settled bets**. One week of NFL gives 14.
This single number is why the leaderboard has no numbers in it, why no strategy is certified, and why
the reward pool is blank.

## 3. What the desk will not do, and why

* **No market price is invented.** The residual columns exist and are empty. A residual is never
  published without the market value it was subtracted from (P-05).
* **No depth rank is invented.** The official Week 11 report gives a practice status for every listed
  player and a game designation for only **16 of 253** rows. It gives no depth rank, starter flag, snap
  share or replacement name. Those columns are blank for all 253 rows, and the 1st-4th string
  deficiency matrix is **not built**, because building it would fabricate starters no club named.
* **"Not listed" is not "available".** Lamar Jackson is absent from the Week 11 report because he is
  on injured reserve (per the 2026-11-13 league article), not because he is healthy. No reserve list
  is captured, so this is a standing flag (F-13).
* **No win rate or ROI is used for ranking.** Ranking is benchmark-relative Brier skill with a
  game-cluster lower bound and a multiplicity adjustment; signal and staking are separate columns.
* **No backtest figure appears on the leaderboard**, ever (LB-01), and the verifier fails the build if
  one appears.

## 4. Flagged irregularities worth your attention first

| Flag | What it is |
|---|---|
| **F-03** | Two official pages disagree on a stadium name: the schedule page's ticket link says *FedEx Field*, the game centre Game Info block says **NORTHWEST STADIUM, LANDOVER MD**. |
| **F-06** | The home-field term is negative (−0.50 pts) in the 2026 official results. Published, not smoothed. |
| **F-12** | The brief states Kerby Joseph, Cade Mays and D.J. Reed are all designated **Out** for Detroit. At the Week 11 read, Joseph and Reed show practice status with a **blank** game status, and Mays is DNP with a blank status. Neither claim is asserted; both are quoted and flagged. |
| **F-13** | Absence from the injury report is being read as health by every desk that does not hold a reserve list. |
| **F-21** | The totals estimators lose to a constant mean on the only holdout that exists. |
| **F-22** | Game designations cover only 2 of the 13 fixtures at this point in the week. |
| **F-23** | The scheduled byte-level capture cannot run from the build sandbox (all five official URLs failed TLS); the failure is left in the ledger as evidence rather than hidden. |

## 5. What would change the picture fastest

1. **A licensed price feed** (suggestion P01). It unblocks G4, every residual, every CLV claim and the
   entire staking layer. Nothing else on this desk is as valuable per dollar.
2. **An official depth source verified for all 32 clubs, or official snap counts** (P02). Snap counts
   are the preferred route because they are a playing-time measure, not a club's opinion.
3. **A second season of official finals** (P05). It is the only route to the 5,773-bet threshold, and
   therefore the only route to a defensible skill claim.
4. **Archived designations joined to inactive lists** (P03, question Q08). Without it, "Questionable"
   stays an unquantified word, and the injury signal cannot be a surprise — only a level.

## 6. Honest bottom line

The desk can originate a line and prove its arithmetic. It cannot yet prove its lines are good,
because it has no market to beat and no sample to beat it with. Stating that plainly — with the
gate, the number that would clear it, and the source for every value — is the product.

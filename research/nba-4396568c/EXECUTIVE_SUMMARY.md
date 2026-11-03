# Executive summary - NBA Desk (session 4396568c)

Data as of 2026-11-03 UTC. Live site: https://sassnarep3-star.github.io/Own5/nba-desk/index.html

## Bottom line

The desk originates its own NBA lines from official NBA team data and publishes 16 (11/04-11/05). It cannot yet show that any line, single, parlay or prop combo has an edge: there are no verified market quotes, so closing-line value is not computable and 0 of 6 pre-registered strategies qualify. 0 rewards are awarded; the pool is unfunded.

## How lines are made

Team rating = in-season points margin blended with a prior of 0.54 x last season's margin (weight on the current season = G/(G+7.5), G = games played), plus home-court advantage of 1.92 points (from 55.4% home wins in 2025-26). Win probability = normal CDF of margin / 14.1.

## Does it work?

Partly, and the sample is small. Early 2026-27 margins correlate r = 0.43 with 2025-26 margins (n = 30). On 22 played games the prior-only model beat an HFA-only baseline by 1.05 points of margin error (z = 1.22, not significant). On totals there was no gain (z = 0.10) and a +9.7 point bias from last season's higher scoring level.

## Correlations

Team-season: win % tracks points margin at r = 0.92 to 0.98. Team-game and spread/total-leg correlations from 22 games have intervals spanning zero. Parlay arithmetic is tabulated by leg correlation. Player-prop and same-game-parlay correlations are blank and flagged.

## Removing luck

Break-even at -110 is 52.38%. A true 55% bettor needs about 2270 settled bets for an 80%-power test. With 100 pure-luck entrants the best is expected to hit about 62% over 100 bets. Rankings therefore use closing-line value with a lower confidence bound, minimum sample, multiple-testing penalty and frozen pre-registration.

## Repo audit

arXiv:2606.27957 figures cited in docs (B2B 44%, P(W|W) 54.5%) verified against the paper; PubMed and arXiv:1910.08858 exist but the docs' attribution/claim wording is partly unverified; 15 of 21 listed sources are third-party commercial pages. Official 2026-27 injury page confirmed.

## Flags

14 flags, none blocking. Top three: no market quotes (F01); 0 qualified strategies and unfunded rewards (F02); 22-game sample is underpowered (F04). Injury reports for 17 teams were not yet submitted when captured, and lines are not injury-adjusted (F05).

## Next steps

Capture timestamped quotes; settle the 16 ledger games from official pages (python3 nba-desk/settle.py); extend the game sample; add a player-value model for injuries; collect a large official player-game sample for prop correlations.


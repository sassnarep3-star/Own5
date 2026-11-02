# Bet Markets & Grading Rules — Verified Research (T3)

Definitions and grading rules below are quoted/paraphrased from **official sportsbook operator pages and regulator-approved house rules** — not from third-party blogs. Machine-readable: `data/bet-types.csv`, `data/bet-combos.csv`.

**Where lines come from:** the NFL's Official Sports Betting Partners (Caesars, DraftKings, FanDuel) all use the NFL's official league data feed [NFL.com](https://www.nfl.com/news/nfl-announces-tri-exclusive-sports-betting-partners). Live NFL lines are published on the operators' own pages, e.g. [DraftKings NFL](https://sportsbook.draftkings.com/leagues/football/nfl) and [FanDuel NFL](https://sportsbook.fanduel.com/navigation/nfl). Line **values** are dynamic and are not snapshotted in this repo (flag F02).

## Market definitions

- **Point spread** — wager on margin of victory; favorite gives points (minus), underdog gets points (plus); half-point spreads prevent a push. [DraftKings NFL page](https://sportsbook.draftkings.com/leagues/football/nfl)
- **Moneyline** — pick the outright winner; margin irrelevant. [DraftKings NFL page](https://sportsbook.draftkings.com/leagues/football/nfl)
- **Total (over/under)** — combined points of both teams. FanDuel notes these markets are powered by official NFL data. [DraftKings](https://sportsbook.draftkings.com/leagues/football/nfl) · [FanDuel](https://sportsbook.fanduel.com/navigation/nfl)
- **Parlay** — 2+ legs combined into one wager; **every leg must win** (minimum two legs). [FanDuel parlay guide](https://www.fanduel.com/sports-betting-guide/what-is-a-parlay-bet)
- **Same Game Parlay (SGP)** — multiple bets from the **same game** (props, spread, totals); the book builds correlation assumptions into the odds, so check the combined price. **SGP+** stacks multiple SGPs across games. [FanDuel NFL guide](https://www.fanduel.com/sports-betting-guide/how-to-bet-on-nfl)
- **Teaser** — adjust spread/total by a set number of points (typically 6) across ≥2 legs for reduced odds; **most common NFL margins of victory are 3 and 7** — the key numbers teasers cross. [FanDuel NFL guide](https://www.fanduel.com/sports-betting-guide/how-to-bet-on-nfl)
- **Player props** — player/team performance (passing yards, rushing yards, TDs, sacks...). [DraftKings](https://sportsbook.draftkings.com/leagues/football/nfl)
- **Live (in-play)** — wagers after kickoff across spread/ML/total/period markets/eligible props. [DraftKings](https://sportsbook.draftkings.com/leagues/football/nfl)
- **Round robin** — multiple smaller parlays built from one selection pool. [FanDuel NFL guide](https://www.fanduel.com/sports-betting-guide/how-to-bet-on-nfl)

## Grading rules (what actually settles a bet)

- **Overtime counts** for full-game spread, moneyline and totals (graded on final official score inclusive of OT). [FanDuel grading FAQ](https://sportsbook.fanduel.com/navigation/nfl) · [FanDuel house rules](https://www.fanduel.com/fanduel-sportsbook-house-rules-on) · [BetMGM rules](https://massgaming.com/wp-content/uploads/BetMGM-House-Rules-8.14.25.pdf)
- **Push**: whole-number spread or total landing exactly on the number → wager refunded; in a parlay the leg is excluded and the parlay re-priced. [FanDuel house rules](https://www.fanduel.com/fanduel-sportsbook-house-rules-on) · [FanDuel NFL guide](https://www.fanduel.com/sports-betting-guide/how-to-bet-on-nfl)
- **Tie after OT**: moneyline wagers void (stake refunded); spread/total settled on posted numbers (push if exactly on the line). [FanDuel grading FAQ](https://sportsbook.fanduel.com/navigation/nfl)
- **Postponed before kickoff → all wagers void**; **relocated but played on the scheduled date → action** (graded on the official league box score, not the venue). [FanDuel grading FAQ](https://sportsbook.fanduel.com/navigation/nfl)
- **Minimum play**: pro football results are official after **55 minutes** unless an official result is declared earlier. [BetMGM regulator-approved house rules (MA)](https://massgaming.com/wp-content/uploads/BetMGM-House-Rules-8.14.25.pdf)
- **Player props**: void if the player is not listed as active by the official league scoring source. [BetMGM rules](https://massgaming.com/wp-content/uploads/BetMGM-House-Rules-8.14.25.pdf); official stats via Elias Sports Bureau [NFL stat corrections](https://fantasy.nfl.com/research/statcorrections)
- **Correlated legs**: parlays containing selections where one outcome directly affects another are **not permitted unless explicitly offered** (e.g., as an SGP); if accepted in error the book may void the bet or settle affected selections as singles. Books also reserve the right to refuse or limit any parlay. [FanDuel house rules](https://www.fanduel.com/fanduel-sportsbook-house-rules-on)

## Combo policy used by this project

<!-- TABLE:bet-combos.csv -->

<!-- TABLE:bet-types.csv -->

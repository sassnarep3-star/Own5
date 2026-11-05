# NBA Strategy Lab — executive summary

**Review date:** 2026-11-05  
**Status:** research only; **0 of 9 strategies qualified; 0 rewards issued**.

## Decision

The repository supports reproducible NBA research lines and historical signal diagnostics, but it does **not** support a claim of profitable or selectively skill-based betting. No verified sportsbook prices, prospective timestamped bet ledger, current availability refresh, or independent replication is present. Market values, ROI, ranks, scores, and rewards therefore remain blank.

## Evidence and outputs

- Frozen official-source input: **275 rows** — 90 NBA team-season rows, 44 team-game rows (22 games), 125 player-game rows, and 16 schedule rows. Each row has a direct official NBA URL.
- Independent integrity suite: **547 checks, 0 failures**. Checks cover official HTTPS hosts, GP = W + L, league wins = losses, unique player-games, scoring identities, rebound identities, paired opponents, and schedule coverage. These are internal checks, not a substitute for opening every external page.
- Archived line set: **16 games** on 2026-11-04/05. Model margins use current margins shrunk toward 2025-26 margins with 20 prior games and zero home-court advantage. The normal probability scale is the 14.3454-point RMSE from the 22-game prior-only diagnostic. These are analyst-derived, unvalidated values, not NBA or sportsbook lines.
- Strategy catalog: **9 candidates** — three team singles, one daily two-leg parlay, two player-prop singles, and three player-prop combinations. Event-level ledgers and all gate outcomes are published.
- Correlation catalog: **22 diagnostics**. In the pooled two-player sample, 25+ points and 3+ made threes has φ = 0.4733, joint hit rate 0.6480, independence product 0.5591, and lift 1.1590 (n = 125). This demonstrates why independence multiplication can misprice that historical combo; it does not establish future profitability.
- Luck controls: chronological player splits, fixed thresholds, exact one-sided binomial tails, Holm correction across nine candidates, Wilson intervals, a 200-event minimum, and a prospective-replication gate. Luck cannot be literally eliminated.

## Competition policy

Raw hit rate is not a ranking metric. An entrant must pass every applicable gate before receiving a score. The proposed future score is `100 × max(0, CI lower bound − null rate) × ln(1+n)` and the proposed funded-pool allocation is 50% / 30% / 20% for the top three qualified entries. Neither scoring nor rewards activates in this snapshot.

## Important flags

F01–F09 are published on the site's **Flagged for Review** page. Material items are absent market/settlement evidence, small retrospective samples, no current availability refresh, zero-HFA and diagnostic-scale conventions, two-player convenience sampling, and no fresh external source fetch in this session. Archived schedule blanks are retained rather than inferred.

## Manual review

Start at [the official source register](../../nba-strategy-lab/sources.html), open the NBA link on each row, and compare it with the frozen input. The session did not freshly fetch external NBA pages; it reused reviewed repository snapshots and independently recomputed internal identities. No broader claim is made that all historical NFL/NBA content elsewhere in the repository was re-certified.

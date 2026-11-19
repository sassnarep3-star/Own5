# NFL Line-Gate Desk — executive summary

Session `af9a1ada`. Desk: `nfl-af9a1ada/`. Built 2026-11-19, before the Week 11 Thursday kickoff.

## The finding, in one line

**The market wins, and the size of its win is measured rather than asserted.**
On 6,711 walk-forward games the model's Brier skill against the closing line is **-0.066**
(interval -0.09 to -0.04); on totals it is **-0.051**. Its margin error is **10.97 points**
against the closing line's **10.25**.

## What was built

| Layer | State |
|---|---|
| Official reads | standings (32 clubs, identities hold: W = L = 149, PF = PA = 6,923), Week 11 slate (13 games, 6 byes), Week 11 injury report (255 rows, 26 clubs), Week 10 finals (14, reconciled 14/14) |
| Prices | 2 books × 13 games, one read at 2026-11-19T11:42:16Z, 156 printed numbers, hashed, with the board's own kickoff string stored beside each |
| Model | opponent-adjusted offence/defence, two-season window, walk-forward, `mu` 22.44, `hfa` +1.17 |
| Origination | side → total → moneyline, 39 rows, fair/market/difference in one convention, inputs hash per row |
| Competition | 7 pre-registered strategies, 5 divisions, gates G1–G8, demotion gate, 0 settled bets, 0 certified |
| Availability | 255 player rows, 16 printed game statuses, 2 clubs printing "No Injuries Reported" |
| Depth | **1 of 32** club charts read; 12 verified ranks; **0 inferred** |
| Registers | 62 requirements, 16 questions, 10 suggestions, 16 flags |
| Site | 14 pages, no JS, table-first, every blank labelled |
| Verification | 1,898 fail-closed checks, 30 unit tests, both green |

## The seven defects this desk found in its own build

Each one is now covered by a test, because each one shipped past a review of a desk like this.

1. A league average inside a *difference* — inflated every predicted margin by ~22 points, saturating probabilities at 0.96.
2. A plus-signed defence — produced a "defence" column that correlated **positively** with points allowed (+0.76).
3. Sum-to-zero by elimination — parked the invariant on the last club alphabetically, which came out at **−18.8**.
4. Fitting on 28 seasons — corr(offence, points-for) = **0.027**; Jacksonville scored 29.9/game and got a *negative* offence.
5. A benchmark probability centred on the close — produced an impossible **+0.30** skill on a closing line.
6. Fair line as a home margin, market line as a printed line — every sign inverted, inventing **23-point edges** on games the two agreed about.
7. Corpus spread sign read the wrong way round — a closing-line MAE of **14.6**, which no real line produces.

## What is not done, and why

Depends on reads the desk has not made (each is one page read):

- depth for 31 clubs → blocks R06, R27, R42, R48
- inactive lists → blocks R21, R29, R41, R49
- a second dated injury read → blocks R11, R56
- operator terms → blocks R20, R36

Depends on the owner: the reward pool, the approver for a registration change, and whether to consolidate the repository's duplicate desks.

Depends on time: every competition question, because there are zero settled bets.

## Where to read more

- `nfl-af9a1ada/index.html` — dashboard, verdict first
- `nfl-af9a1ada/flagged.html` — 16 items, including all seven defects
- `nfl-af9a1ada/research.html` — method and the defect table
- `nfl-af9a1ada/suggestions.html` — 10 owner decisions, none implemented

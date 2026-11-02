# Verification record

Review date: **2026-11-02 UTC**. Reviewer/integration owner: `arena-cd43258e`.

## Scope and standards

- Initial repository audit: the only tracked file was `README.md`, six bytes, containing `# Own5`. There was no existing dataset or strategy to validate.
- Every data record and generated table row was checked for an official publisher reference. These references support only the specific published facts or methodological concepts recorded. Proposed strategy descriptions, gate thresholds, ranking policy and reward badges are **project designs**, not externally verified NFL facts.
- No numerical player statistics, prices, fitted probabilities, empirical correlations, return statistics or prize amounts were imported. All unavailable empirical fields are `null` and display as blank cells. There are zero prediction records, not a populated model ledger.
- No claim is made that every line of every external site was verified. The checked **finding** and **limitation** in each of the 14 primary-source records define the external review scope. The relevant source text was read, rather than treating URL availability as proof.

## Primary-source excerpt ledger

Short excerpts from retrieved official pages are preserved below to make the source checks reviewable. The source register provides the complete claim and limitation. Pages can change after this review; these are selected text excerpts, not full raw-page archives or independently timestamped legal evidence.

| Source ID | Primary publisher link | Excerpt read | What it supports |
|---|---|---|---|
| REPO-AUDIT | [Official GitHub repository tree API](https://api.github.com/repos/sassnarep3-star/Own5/git/trees/426b19d4981627243aa21b324903eab97cfb9d13) | The tree lists only `README.md`, blob size 6 bytes. | Direct primary evidence for the empty starting repository; not an NFL-data claim. |
| NFL-RULES | [NFL Football Operations](https://operations.nfl.com/rules-officiating/2026-nfl-rulebook) | “2026 NFL RULEBOOK”; “Explore the official 2026 NFL rulebook.” | Current rulebook identity and linked PDF, not operator settlement. |
| NFL-NGS | [NFL Next Gen Stats](https://nextgenstats.nfl.com/glossary) | “Time to Throw measures the average amount of time elapsed from the time of snap to throw on every pass attempt for a passer (sacks excluded).” | F01 definition; other F02–F09 definitions were checked in their respective glossary paragraphs. |
| NFL-INJ | [NFL.com injuries](https://www.nfl.com/injuries/) | “2026 NFL Injury Report”; “Injuries - WEEK 8”; table columns “Practice Status” and “Game Status”. | Presence and scope of the current report, not historical status at decision time. |
| NFL-SCHED | [NFL.com schedules](https://www.nfl.com/schedules/) | “SCHEDULE2026”; “By Week”; “Team Schedule”. | Schedule/year/week navigation and game links. No score history used in a model. |
| NFL-STATS | [NFL.com player stats](https://www.nfl.com/stats/player-stats/) | “2026 Player Stats - Category”; “Passing”; links to “Rushing” and “Receiving”. | Category availability; the extracted numeric table lacked headers, so values were excluded. |
| DK-GENERAL | [DraftKings general rules](https://sportsbook.draftkings.com/help/general-betting-rules/general-rules) | “DraftKings Virginia Sportsbook House Rules”; “only while you are physically located in the Commonwealth of Virginia”. | Jurisdiction-specific scope and rule hierarchy, not eligibility elsewhere or access to executable quotes. |
| DK-MARKET | [DraftKings market rules](https://sportsbook.draftkings.com/help/general-betting-rules/market-rules) | “If a whole number is offered as the point spread or handicap, bets will be settled as Push if the outcome bet on is tied after the point spread or handicap for the bet has been applied.” | F10; total-points equality-as-Push was separately checked under Total Points Markets for F11. |
| SK-CV | [scikit-learn cross-validation](https://scikit-learn.org/stable/modules/cross_validation.html) | “Learning the parameters of a prediction function and testing it on the same data is a methodological mistake”. | Held-out evaluation and overfitting caution. |
| SK-TIME | [scikit-learn TimeSeriesSplit](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html) | “To ensure comparable metrics across folds, samples must be equally spaced.” | Need for chronological/custom NFL splits, not random row folds. |
| SK-CAL | [scikit-learn calibration](https://scikit-learn.org/stable/modules/calibration.html) | “A lower Brier loss, for instance, does not necessarily mean a better calibrated model”. | Scoring rules need reliability analysis, not Brier alone. |
| SC-CORR | [SciPy pearsonr](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html) | “Pearson product-moment correlation coefficient”; “The correlation coefficient is not defined in this case, so np.nan is returned.” (constant input warning) | Linear association, undefined constant inputs and interval support. |
| SC-BOOT | [SciPy bootstrap](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html) | “take a random sample of the original sample (with replacement) of the same size as the original sample.” | Resampling definition; game/week clustering is a project adaptation requiring additional implementation. |
| SM-MULTI | [statsmodels multipletests](https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html) | “holm : step-down method using Bonferroni adjustments”; “fdr_bh : Benjamini/Hochberg”. | Correction method availability; no empirical tests were run here. |

## Irregularities found during research

1. The attempted [Football Operations injury-policy URL](https://operations.nfl.com/inside-football-ops/players-legends/player-health-safety/nfl-injury-report-policy/) returned only “Skip to main content”. It is not treated as a checked policy; the readable official injury report is the fallback reference. Published as R05.
2. An exploratory NIST URL returned a page titled “Measures of Skewness and Kurtosis”, not correlation. It was excluded rather than cited for an unrelated claim. NIST reference-dataset material was also not used to establish NFL signals.
3. Player-stat extraction omitted numeric table headers. Columns were not guessed and no numbers were used. Published as R09.
4. Operator rules explicitly scoped themselves to Virginia. No generalization to other operators or jurisdictions. Published as R08.
5. A first coordination push attempt found that the new session branch did not yet exist remotely. Rebased against `origin/main` and performed the initial push of the fixed session branch; no conflict and no other files were overwritten. All subsequent pushes rebase against the session branch first.
6. The first browser test could not load system NSS/NSPR libraries. Fixed the test harness to use the browser package’s bundled support libraries in a temporary directory. Subsequent real-browser checks passed. This was a test-environment issue, not a broken website build.

## Integration verification

- `python scripts/seed.py`: deterministic reviewed register with 14 sources, 11 definitions, 8 strategies, 7 gates, 6 correlation questions, 5 market methods, 10 flags and 5 competition policies.
- `python scripts/build.py`: deterministic static build of landing page and seven subpages; no runtime dependency on a feed, secret or third-party script.
- `python -m unittest discover -s tests -v`: 27 tests covering pricing identities, invalid inputs, undefined correlations, complete settlement probabilities, scoring, Holm correction, fail-closed gate declarations, source coverage, null handling, unique IDs, all local links and fragment targets.
- `node --check assets/app.js`: JavaScript syntax checked.
- `npm run test:browser`: real Chromium desktop and mobile visits to all eight routes; tests source-link coverage, no page overflow, no runtime errors/local asset failures, search, market and severity filters, empty state, CSV source URL preservation, blank empirical cells and no-JavaScript source rendering.
- Desktop and mobile screenshots inspected visually. Browser screenshots are ignored scratch artifacts, not committed research evidence.
- The CI workflow reruns build, Python tests and browser smoke tests before merge. External URLs were checked through the source-reading tools during research, not through a claim that the local link checker can prove external content. Live Pages deployment and PR outcome are recorded in the coordination board.

## Completion interpretation

The **site, source audit, proposed methods, validation specification, test suite and publication** can be completed in this session. Empirical model fitting, historical performance evaluation, measured correlations and funded rewards **cannot** be claimed complete without the required evidence. These remain explicit nonblocking review items. No user input or credentials are requested to browse this research deliverable.

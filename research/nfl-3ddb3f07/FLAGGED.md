# Flagged for review — integration session 3ddb3f07 (2026-11-19)

Items this session found that a reviewer should look at. They are published, not blocking,
and none of them was silently corrected.

## I3-F1 · The pre-registration chain is broken (BLOCKING for certification)

**What was found.** `nfl-command-desk` published a pre-registration commit hash
(`4078a9ad`, republished on 2026-11-18 as `e7282e35…`) and a gate (V11) that proved the
hash existed and was an ancestor of HEAD. Both hashes were orphaned when the branch was
rebased on 2026-11-18, so V11 could never pass again and the published proof of
pre-registration could no longer be produced from the repository.

**What was done.** V11 now proves what is still provable: the rule text in
`nfl-command-desk/data/preregistration.csv` is byte-identical to the file at the freeze
commit the site publishes, that commit is in the current history, the site quotes it, and
the site states that the original registration was orphaned and that **no strategy may be
certified on the basis of a pre-registration hash**. `FLAG-V11` is on the desk's flagged
register.

**What is still open.** A commit message cannot be used to re-create a pre-registration
that happened before the results were seen. The only honest remedy is to re-freeze the
rules in a fresh prospective window whose registration commit is never rewritten.

**Source.** <https://github.com/sassnarep3-star/Own5/blob/main/nfl-command-desk/data/preregistration.csv>
· <https://github.com/sassnarep3-star/Own5/blob/main/nfl-command-desk/verify.py>

## I3-F2 · The daily capture job destroyed the evidence it was meant to keep (REVIEW)

**What was found.** The `Own5 hub - daily official capture` workflow captured the official
pages, then rebuilt the pages, and only then committed. The scheduled run of 2026-11-19
failed in the rebuild step (11 seconds in), so the capture was never committed: the ledger
lost a day's read and the job failed without leaving evidence in the repository.

**What was done.** The workflow now commits the immutable capture first and rebuilds the
pages from it afterwards, so a rebuild failure can no longer discard a capture. The capture
step's own output is still printed, and the job still fails loudly.

**What is still open.** The root cause of the rebuild failure is not known: the runner log
host is not reachable from this environment, so the step's output could not be read. Two
defects that would produce it were repaired — a capture that no longer parses now becomes a
recorded failed capture instead of an exception, and the published capture summary is now
derived from the ledger instead of being a hand-written string — but the failure itself
remains unexplained and will be visible in the next scheduled run.

**Source.** <https://github.com/sassnarep3-star/Own5/blob/main/.github/workflows/own5-hub-capture.yml>

## I3-F3 · The repository-wide line-hash audit is a merge-time tripwire (REVIEW)

**What was found.** `nfl-b34253a1` pins the sha256 of every physical line of every file in
its scope (about 103,000 lines). Any merge that touches one of those files fails the B34
check until the audit is regenerated. The audit itself is excluded from its own scope, so
regenerating it is safe — but every session that merges has to know to do it, and several
have discovered it the hard way.

**What was done.** This session regenerates the audit as its last step, after every other
change is committed. The rule is recorded in `COORDINATION.md`.

**What is still open.** The design is left as it is: the audit's value is that it is a
frozen snapshot of a point in time. The cost is that it must be refreshed after every
merge that touches its scope.

**Source.** <https://github.com/sassnarep3-star/Own5/blob/main/nfl-b34253a1/audit_repo.py>

## I3-F4 · 127 broken links were live on the site (REVIEW, fixed)

**What was found.** Three desks published anchors whose `href` was prose rather than a URL
(`href="n/a - deliberately omitted"`, `href="official NFL abbreviation ARI"`), links that
resolved one directory too high (`nfl-desk-e1d60f5d`, eight pages), and a repo-relative
link that 404ed from its served location (`nfl-desk-ccc5caf2`). The repository's own
`nba-commission` verifier had been reporting all 127 as failures for days, and the failures
were dismissed as a defect in that desk's scanner.

**What was done.** Each defect was repaired in the owning desk's own generator, each desk
was rebuilt and re-verified with its own verifier, and `nfl-desk-864d5668` gained a
regression guard that fails on any `href` that is not a path or a URL.

**What is still open.** Nothing for these three desks. The lesson is recorded: a source
column that may legitimately hold prose must not be linkified blindly.

**Source.** <https://github.com/sassnarep3-star/Own5/blob/main/nfl-desk-864d5668/build_site.py>

## I3-F5 · Three requirement registers, no verified crosswalk (REVIEW)

**What was found.** The repository holds three requirement registers of different shapes:
the market desk's 78 rows, the Own5 hub's 80 rows and the command desk's 73 rows. The
integration hub's own suggestion SG-A62-01 already asked for a row-by-row crosswalk
before any combined completion count is published.

**What was done.** The front door publishes one canonical register (the market desk's 78
rows, whose columns carry the gate and the clearing number the brief asks for) and links
the other two. No combined count is published.

**What is still open.** The crosswalk. Until it is done row by row, "the project is 40%
done" is not a statement anyone can check.

**Source.** <https://github.com/sassnarep3-star/Own5/blob/main/nfl-market-desk/data/decision_readiness.csv>

## I3-F6 · The root landing page was stale (REVIEW, fixed)

**What was found.** `index.html` was stamped "Reviewed 2026-11-02" and linked no desk newer
than 2026-11-17, so the front door of the site did not lead to the work that followed.

**What was done.** The generator (`scripts/build.py`) now points the notice at the front
door, the integration hub, the desk directory and the repo review, and the page carries the
review date 2026-11-19. The other seven pages of that workspace are unchanged.

**Source.** <https://github.com/sassnarep3-star/Own5/blob/main/scripts/build.py>

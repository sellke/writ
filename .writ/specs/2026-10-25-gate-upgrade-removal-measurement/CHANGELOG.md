# Changelog: Gate Upgrade Removal Measurement

## 2026-11-09: Repro First substitute baseline (`/edit-spec`)

- **Change type:** adding scope, reorganizing stories
- **Why:** the first trial never exercised Repro First (no baseline story was a bug fix). The `amend` ack (Business Rule 7) left the spec open until a substitute baseline was added (drift-log DEV-013).
- **What changed:**
  - spec.md: status line; Must Include item 7; Scope Boundaries; Business Rules 1, 7, 9 (delegated labels for the substitute run), 10, and 13; new Business Rule 14 (selection rule and the four admitted yuss stories); Journey step 8; Detailed Requirements for Stories 5 and 6.
  - spec-lite.md: deliverable, files in scope, business rules.
  - sub-specs/technical-spec.md: `init --upgrades`; new § Repro First Substitute Trial; Verdict Execution commit order; outcome-test source; error map, shadow paths, and files in scope.
  - Story 4: AC-4.5 retired, task 4.6 removed, task 4.7 tags updated; status Completed. `Verified by:` lines added for AC-4.3 and AC-4.4: with the story Completed, `ac-trace.py` reported both as blocking `untested_criterion`.
  - Story 5 (new): run the Repro First substitute trial.
  - Story 6 (new): act on Repro First's verdict; delete the harness.
  - user-stories/README.md: table, totals, dependencies.
- **Unchanged:** Business Rule 5 (a catch needs a repro that fails at the parent and still fails at the story commit); `trial-report.md`; the other three verdicts.
- **AC IDs assigned:** Story 5: AC-5.1 to AC-5.5. Story 6: AC-6.1 to AC-6.5.
- **AC IDs retired:** Story 4: AC-4.5 (its harness-deletion criterion moved to AC-6.5).
- **Retired-ID citations left in place:** drift-log.md DEV-013 and Story 4's "What Was Built" (historical records); uat-plan.md lines 281, 1020, 1048, 1099 (the UAT plan predates Story 4 and needs regenerating).
- **Backup:** `backups/2026-11-09-repro-first-substitute/`

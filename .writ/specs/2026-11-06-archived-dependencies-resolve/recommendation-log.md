# Recommendation Log: Archived Dependencies Resolve

> Mode: `/create-spec --from-issue .writ/issues/bugs/2026-11-06-archiving-a-spec-breaks-its-dependents.md`
> Authorized by: the maintainer's contract lock on 2026-11-06 ("Lock contract and create spec package", doubt log `6309cdbfb162`)
> ADRs: [ADR-033](../../decision-records/adr-033-doubt-gated-autonomy.md)

Doubt-log ids are rows in `.writ/state/doubt-log.jsonl`. Jev is uncalibrated, so both `direction` decisions asked and were answered as recommended; the `plan` decision acted.

| # | Decision | Evidence | Material alternatives | Risk / reversibility | Result |
|---|---|---|---|---|---|
| 1 | Fix the reader: `spec-deps.py validate` resolves an id under `.writ/specs/archive/` as satisfied. `archive-sweep.py` unchanged | Doubt log `d1b4b8d24b67`, asked, as recommended. The issue lists this outcome first. Archive eligibility is complete-family only (`spec-lifecycle.md`), so an archived dependency is satisfied by definition. A dependency is complete before its dependents, so refusing archival would block `/release` Step 1.3c in the common case. `ac-trace.py` already resolves both locations | Refuse to archive while a dependent is open; rewrite the dependent's header | Low. One lookup in a read-only script; every blocker kept | Fix in `validate` |
| 2 | Location alone satisfies; no status check on archived folders | `validate` never checked an active dependency's status either; completeness is `/verify-spec`'s concern; eligibility already gates on status | Call `spec-status.py is-complete` on the archived file | Low. A hand-moved open spec is a lifecycle violation, not this script's | No status check |
| 3 | Archived specs are never parsed | Keeps the archive inert for ordering; an archived malformed header must not block an active phase | Parse archived headers for their own edges | None | Names only |
| 4 | Active folder wins when an id exists in both places | `archive_one()` reports that state as `collision`; the active folder is the one `_discover` sees | Prefer the archive; block | None | Active wins |
| 5 | `archived_dependencies` is additive; schema stays `spec-deps-graph-v1`; `graph` keeps declared lists | `phase-state.py` consumes `order` only; no consumer reads a schema bump | Bump to v2 | None | Additive |
| 6 | Contract locked as drafted | Doubt log `6309cdbfb162`, asked, as recommended | — | None | Locked |
| 7 | One story, seven tasks | Doubt log `aae3072d3a88` (`plan`, acted). Issue Effort Small; the docs lines carry no value apart from the behavior | Two stories (code, docs) | Low | 1 story, 7 tasks, 5 criteria |
| 8 | Tests in both pytest (new `test_spec_deps.py`) and `eval-spec-deps.py` scenarios | CI runs both `eval.sh` and pytest 3.9; `spec-deps.py` had eval scenarios but no pytest file; `test_story_deps.py` is the recipe | Eval scenarios only | None | Both |
| 9 | Restore `2026-10-25-design-divergence` to the removal-measurement header as the real-repo check | The 2026-11-06 workaround (commit `04e2045`) removed a correct entry; restoring it is the regression the issue reports, run live | Leave the workaround | Low. One header line, git-revertable | Restored in task 1.6 |
| 10 | Visual references: skipped | No UI; Step 1.5 applies only to user-facing UI | — | None | Empty `mockups/` |
| 11 | Sub-specs: `technical-spec.md` only, with the error map | File reads only; no API, database, or UI | — | None | technical-spec only |
| 12 | Dependencies `[]` | No in-progress spec touches the files in scope | — | None | `[]` |
| 13 | Cross-spec overlap: none | No in-progress spec-lite names `spec-deps.py`, `spec-lifecycle.md`, `verify-spec.md`, or `implement-phase.md` | — | None | None |
| 14 | Owner `@AdamSellke` | `git config user.name` = "Adam Sellke" | — | None | Set |
| 15 | Story file written by the spec agent, not a floor-tier generator subagent | One story; the authoring agent had the full contract and the script source in context; Step 2.6a validates the result the same way (precedent: `2026-11-06-pr-ready-and-ledger` decision 28) | Spawn one generator | Low. `ac-trace.py` and `spec-analyze.py` check the file | Written directly |
| 16 | Step 2.4b: nothing to write back | No `Amends:` or `Extends:` line | — | None | Skipped |

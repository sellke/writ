# Gate Evidence

> Spec: 2026-11-06-lean-story-pipeline, Story 1
> Recorded: 2026-11-06
> Rules: spec.md Business Rules 1, 2, 3, 7

One row per `gates:` entry in `commands/implement-story.md`. The **Evidence** cell is the frontmatter `evidence:` value, copied verbatim. The frontmatter names no `.writ/` path, because shipped command files must not link to Writ's own history (`scripts/eval-shipped-refs.py`); the full citation for each catch is under [Sources](#sources).

A catch is a dated artifact that shows the gate changing an outcome (Business Rule 1). Under [Not counted](#not-counted), each item was considered and rejected, with the reason.

Path rule: `full-pipeline` only when the evidence is `none recorded` and no kept gate reads the gate's output (Business Rules 2 and 3). The kept gates are Safety Fact, Reviewer Filters, and the evidence gate, all in Gate 3. Gate 0 Divergence was a removal-trial keep, but the design-divergence blind trial removed it from `implement-story.md` on 2026-11-04, so no entry carries it.

| Gate | Evidence (frontmatter value) | Rule 3 dependency | Path |
|---|---|---|---|
| `gate0_arch` | none recorded | none: no kept gate reads Gate 0's output | `full-pipeline` |
| `gate0_5_boundary` | none recorded | Gate 2.5's crossings check reads this map to set the risk route, and that route turns Safety Fact on | `default` |
| `gate1_coding` | none recorded | produces the code that every kept gate reviews | `default` |
| `gate2_build` | none recorded | the evidence gate re-runs the lint and typecheck commands Gate 2 saves to `.writ/state/gate2-checks-<story-stem>.txt` (`--checks`) | `default` |
| `gate2_5_surface` | none recorded | produces the risk route that turns Safety Fact on, and the blast radius Safety Fact reads | `default` |
| `gate3_review` | lean-story-tasks trial (2026-11-06): evaluator failed a Major data-loss defect, fixed on recode; gate-upgrade trial (2026-11-04): Safety Fact 2 valid catches, Reviewer Filters 1 | holds Safety Fact, Reviewer Filters, and the evidence gate | `default` |
| `gate3_5_drift` | ci-and-update-integrity DEV-007 (2026-10-20): an evaluator Large-drift PAUSE was rejected at Gate 3.5 and recoded, so customized Cursor files are no longer overwritten | none needed: has its own catch | `default` |
| `gate4_tests` | Phase 15 retro (2026-10-30) F26: on 2026-10-26 authenticity blocked a test that imported no source, and the test was rewritten | none needed: has its own catch | `default` |
| `gate4_5_behavior` | none recorded | none | `full-pipeline` |
| `gate5_docs` | none recorded | none | `full-pipeline` |

Result: 7 entries stay on the default path (3 on their own catches, 4 as Rule 3 producers), and 3 move to `full-pipeline`: `gate0_arch`, `gate4_5_behavior`, `gate5_docs`.

## Sources

Each source below was read on 2026-11-06.

- **`gate3_review`**
  - `.writ/specs/2026-11-06-lean-story-tasks/trial-report.md`, "The one substantive difference": in arm-original, Story 1's Gate 3 evaluator failed the story with a Major finding (a recorded baseline that lets a later install overwrite a user edit), reproduced the data loss, and one recode fixed it. The run date is 2026-11-06.
  - `.writ/specs/2026-10-25-gate-upgrade-removal-measurement/trial-report.md` (committed in `ef0c418`, 2026-11-04): `upgrade: safety-fact verdict=keep exercised=4/4 upgrade_only=2 valid=2` and `upgrade: reviewer-filters verdict=keep exercised=4/4 upgrade_only=1 valid=1`.
  - `.writ/specs/2026-10-20-harness-cuts/drift-log.md` DEV-004 (run 2026-10-20): Gate 3 iteration 1 failed on `untested_criterion` for AC-1.5, and the coder added four AC-1.5 tests.
- **`gate3_5_drift`**: `.writ/specs/2026-10-20-ci-and-update-integrity/drift-log.md` DEV-007 (run 2026-10-20). Iteration 1 overwrote a customized Cursor `rules/writ.mdc` and `system-instructions.md` while the notice said they were preserved, and the evaluator returned PAUSE (Large). The orchestrator rejected the deviation against AC-5.3 and Rule 9, and the coder recoded: a differing Cursor unit with no baseline is now preserved. Iteration 2 accepted the entry as Medium. A second catch: `.writ/specs/archive/2026-10-25-design-divergence/drift-log.md` DEV-010 (run 2026-10-26), where Gate 3 cycle 1 returned PAUSE (Large) and the reject path regenerated the trial inputs. `drift-format.py` itself has no recorded catch (see Not counted).
- **`gate4_tests`**: `.writ/retros/2026-10-30-phase-15.md` F26 reports `test_imports_no_source` surfacing after Gate 3 twice, at the cost of a test rewrite. The transcript it cites (`agent-a6d6825f48beed2c0.jsonl`, the Phase 15 design-divergence lane, Story 5, 2026-10-26) shows `test-integrity.py authenticity` flagging `scripts/tests/test_divergence_trial_outcome.py` with "resolves zero module specifiers into project source". The orchestrator then told the coder that Gate 4 blocks, and the test was rewritten before the story commit.

## Not counted

- **`gate0_arch`, agent catches before the script.** `.writ/specs/archive/2026-09-07-phase11-stage2-prune-the-base/drift-log.md` DEV-005 and DEV-006, and `.writ/specs/archive/2026-09-03-model-delegation/drift-log.md` DEV-002 and DEV-003, record deviations found at Gate 0 between 2026-09-03 and 2026-09-07, some applied in commits (`2b11f7d`). The `architecture-check-agent` made them. `arch-check.py` did not exist until 2026-09-08 (`dda5623`), and the agent has run only under `--full-pipeline` since `b99c4a3` (2026-09-09). The script on the default path has no recorded catch. The lean-story-tasks story reports for Stories 1–4 (`.writ/state/story-report-story-{1,2,3,4}.md`, 2026-11-06, local and gitignored) each read `arch-check pass`. Moving Gate 0 to `full-pipeline` keeps the agent that made those catches.
- **`gate0_5_boundary` and `gate2_5_surface`, crossings.** `.writ/retros/2026-10-30-phase-15.md` F13: crossings flagged generated copies in 4 of 4 Phase 15 stories, which sent every story to `review-agent` with no defect behind the routing. That is a false-positive cost, not a catch. Both entries stay on the default path for the Rule 3 dependency only.
- **`gate2_build`, build smoke.** No drift log, retro, or story report records `build_failed_source`. `.writ/specs/archive/2026-09-05-phase11-repair-and-baseline/drift-log.md` DEV-020 (2026-09-06) is a Gate 3 review noticing that the build-smoke call had been dropped. That is a catch for Gate 3, not one for build smoke. The Rule 3 dependency is the saved check-command file, not build smoke's own verdict.
- **`gate3_5_drift`, evidence-gated-review DEV-001.** `.writ/specs/2026-11-04-evidence-gated-review/drift-log.md` DEV-001 (2026-11-04) records a Large drift resolved by a user spec amendment (`b69320b`). The orchestrator raised the conflict right after the Gate 1 hand-back and asked the user directly, and the only Gate 3 review for that story returned PASS, noting DEV-001 was already logged. Neither Gate 3 nor Gate 3.5 changed the outcome.
- **`gate3_5_drift`, the drift-format script.** `.writ/retros/2026-10-30-phase-15.md` F1 records a miss: `drift-format: pass` on 65 `Auto-amended` entries that amended nothing. Commit `687b9f0` (2026-11-04) fixed false `large_drift_without_pause` failures on Stories 2–7 of evidence-gated-review. Neither changed a story outcome for the better.
- **`gate3_review` and `gate3_5_drift`, replayed checks.** `.writ/eval/supervisor-trial/report.md` (2026-11-05) shows today's `ac-trace` and `drift-format` failing Phase 15 lane 1's historical work. The checks were run on work that had already merged, so no outcome changed. The catch in that report belongs to the supervisor, which is not an `implement-story` gate.
- **`gate4_5_behavior`.** `app-verify.py` returned `unverifiable (no_recipe)` in each of the four lean-story-tasks story reports. This repo has no `.writ/docs/app-verification.md` recipe, so the gate has never decided a Writ story.
- **`gate5_docs`.** `docs-check.py` returned `unverifiable` in each of the four lean-story-tasks story reports. No drift log, retro, or commit records a docs-check `fail`.
- **`gate1_coding`.** Gate 1 is the producer, not a check. The lean-story-tasks trial records the coding agent listing the data-loss risk as a concern and implementing it anyway. That counts against Gate 1, not as a catch.

## Kill conditions

`kill_when` is written to be checkable later (Business Rule 7). Story 1 does not build the tally.

- **Gates with their own catch** (`gate3_review`, `gate3_5_drift`, `gate4_tests`): `sole_catches == 0 over 20 default-path records`, read from `story-gate.py tally`.
- **Rule 3 producers** (`gate0_5_boundary`, `gate2_5_surface`, `gate2_build`): `gate3_review` leaves the default path, read from the `gates:` frontmatter. `gate2_build` also needs `sole_catches == 0 over 20 default-path records`.
- **`gate1_coding`**: every other entry leaves the default path, read from the `gates:` frontmatter.
- **Demoted gates** (`gate0_arch`, `gate4_5_behavior`, `gate5_docs`): this file still reads `none recorded` for the gate on 2027-05-06. A `full-pipeline` run writes no `story-gate` record, so this file is the only place a later catch can be recorded.

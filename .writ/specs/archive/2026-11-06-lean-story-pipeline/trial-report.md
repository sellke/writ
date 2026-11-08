# Trial Report: Lean Story Pipeline

> Spec: 2026-11-06-lean-story-pipeline, Story 6
> Run: 2026-11-07
> Procedure: `sub-specs/technical-spec.md` → Trial procedure (Story 6)

## Pick

Rule: an archived spec with at most 3 stories, identifiable implementation commits, and a recorded Gate 3 FAIL or drift entry.

| Candidate | Stories | Why |
|---|---|---|
| `2026-08-13-claude-md-install-merge` | 2 | **Picked.** Base `f054e9d` (parent of its first implementation commit `16048cd`), a drift log, and a known Major data-loss defect: the manifest records a user-edited block's hash, so the next plain install overwrites the edit (lean-story-tasks `trial-report.md` → "The one substantive difference"). The August 2026 implementation shipped it; `a1c900c` fixed it in October. |

The lean-story-tasks trial already screened the other archived specs with 3 or fewer stories; this one is the only one with a recorded Major defect to plant.

## Method

- **Base:** both arms are detached worktrees of `f054e9d`, in the session scratchpad.
- **Spec package:** taken from `16048cd` (the stories as first committed), with Story 1's completion bookkeeping reset. Both arms use the same story files.
- **Pipeline overlay:** one setup commit per arm adds the Writ pipeline files: `commands/`, `agents/`, `skills/`, `adapters/`, `system-instructions.md`, `.writ/docs/`, and every `scripts/*.py`/`*.sh` except `install.sh` and `update.sh`, which the stories change.
  - `arm-before`: from `40b1a7c`, this spec's base.
  - `arm-after`: from `183768c`, Story 5's completion.
  - The two arms differ only in: `implement-story.md`, `implement-spec.md`, the coding, evaluator, review, and supervisor agents, `story-gate.py` (after only), `test-integrity.py`, `verdict-provenance.py`, two adapters, two docs.
- **Run:** per arm, per story in order, `claude -p "/implement-story <story file>" --model claude-opus-5-5 --permission-mode bypassPermissions --setting-sources project,local --output-format stream-json --verbose < /dev/null`. The arms ran at the same time in separate worktrees. Headless mode has no AskUserQuestion, so a question is a stop.
- **Measured with:** the stream-json result events (cost, tokens), the run timeline (wall-clock), a count of `python3 scripts/*.py` calls in the orchestrator's own Bash commands, each session's final report, the arm's git log, and an independent replay of the planted defect: install, hand-edit inside the Writ block, install twice, check whether the edit survives.

## Results

| Measure | arm-before | arm-after |
|---|---|---|
| Blocking findings | 2 (Story 1: the data-loss defect, a Major issue with test evidence under Large drift; Story 2: Gate 4 authenticity on a bash test, a known false positive) | 1 (Story 1: the data-loss defect as a Critical Gate 3 FAIL with test evidence) |
| Escaped Major+ defects | 0 | 0 |
| Review iterations | 2 (Story 1: 1, Story 2: 1) | 3 (Story 1: 2, Story 2: 1) |
| Wall-clock | 984 s (555 + 429) | 1757 s (1022 + 735) |
| Cost and tokens (all agents; orchestrator alone in brackets) | $5.58; 90,994 output, 6.41 M cache-read (40,076; 3.95 M) | $9.37; 155,475 output, 12.65 M cache-read (51,969; 5.63 M) |
| Orchestrator script calls | 29 (11 + 18) | 12 (8 + 4) |
| Gates failed or stopped | stopped at Gate 3.5 (Story 1, Large-drift PAUSE); stopped at Gate 4 (Story 2, BLOCKED on authenticity) | Story 1: Gate 3 FAIL; post-review fail (row 4, `safety_fact_below_floor`), skipped past to the recode; post-review fail after a hand-copied review dropped a test reference; then PASS. Story 2: none. None stopped |
| Stories completed and committed | 0 of 2 | 2 of 2 (`dc0edb6`, `af77d43`) |
| Planted defect in the final tree | present (edit lost on the second install) | fixed (edit survives; covered by a test) |

### What the difference was

- **Story 1.** Both reviewers found the planted data-loss defect and reproduced it. `arm-before`'s review agent filed it as Large drift (DEV-001), so Gate 3.5 paused for accept / reject / modify-spec and the headless run stopped with the defect in the tree. `arm-after`'s review agent filed it as a Critical FAIL with test evidence. One recode kept the previous baseline when a block is preserved, added a test for install → keep → install, and passed round 2.
- **Story 2.** Both reviews passed. `arm-before` then stopped at Gate 4: `test-integrity.py authenticity` flagged its new bash test, the false positive `story-gate.py` now filters out of the authenticity input (Story 3, `112ee2b`; extended to `check --tests` in DEV-019). `arm-after`'s post-review passed and the story committed.
- **Orchestration.** `arm-after`'s orchestrator made 12 script calls for two completed stories, including a recode. `arm-before`'s made 29 for two stories that each stopped after one review.
- **Same in both arms (spec problems, not pipeline):** an unmodified pre-fix `CLAUDE.md` ends up with Writ's content twice; `update.sh` exits before its restore path when `CLAUDE.md` is missing.

### What got worse

- **Cost** was 1.68 times, all-agent output tokens 1.71 times, and wall-clock 1.79 times higher in `arm-after`, because it did more work: a recode, two end-to-end installer runs by its agents, and two completed stories against none. The trial does not measure cost per completed story fairly, because `arm-before` stopped early on both stories.
- **Process deviations in `arm-after`:**
  - After round 1, post-review asked for a safety-fact re-spawn of the reviewer, and the orchestrator skipped it and went straight to the recode.
  - The orchestrator hand-copied the round-2 review into the review file and dropped part of a test reference. Post-review failed on it until the exact text was restored, so the runner caught the excerpt problem that Phase 15 retro F8 describes.

## Limits

- **Sample size: one spec, two stories, one run per arm.** Model variance alone could explain the Story 1 difference between a Large-drift PAUSE and a Critical FAIL. The trial can show a regression; it cannot prove an improvement.
- The Story 2 difference is mechanical: `arm-after`'s runner leaves shell tests out of the authenticity input. A rerun would most likely give the same result.
- Both arms ran at the same time on the same account; neither run was retried.
- `arm-before`'s Story 2 ran on a tree that still held Story 1's uncommitted, paused work; `arm-after`'s Story 2 ran on a committed Story 1.
- The arm commits (`6cfb1e1`, `2c63dfa`, `dc0edb6`, `af77d43`) are unreachable since the worktrees were removed, and the session streams are kept only in the session scratchpad; `git gc` can prune the commits.
- **Full suite:** the full pytest suite was not run on either arm. Each arm mixes an August 2026 tree with an overlay of today's pipeline scripts, so suite failures would come from the mix, not from the stories. The escaped-defect check is the planted-defect replay plus each arm's story and regression bash tests, all of which pass in both arms (`arm-before` passes them with the defect present).
- **Script-call count:** counted from the orchestrator's own Bash commands; subagents' calls are not in the stream.
- **Token basis:** a resumed session writes several result events; per-event `usage` covers that segment and is summed, while `modelUsage` and `total_cost_usd` are cumulative and read from the last event.

## Verdict

`arm-after` finished both stories and fixed the planted Major defect with a test. `arm-before` caught the same defect but stopped on both stories, one at a Large-drift pause and one on a known false positive. `arm-after` made 12 orchestrator script calls against 29. Escaped Major+ defects are 0 in both arms, so this is not a regression. Cost and wall-clock were higher in `arm-after` because it completed more work. Sample size: one spec, two stories, one run per arm.

lean-pipeline: keep

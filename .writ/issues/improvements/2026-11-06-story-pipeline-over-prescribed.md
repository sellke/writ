# Story Pipeline Orchestration Is Over-Prescribed for Current Models

> **Type:** Improvement
> **Priority:** High
> **Effort:** Large
> **Created:** 2026-11-06
> **spec_ref:** .writ/specs/2026-11-06-lean-story-pipeline/spec.md

## TL;DR

`/implement-story` gives the orchestrator a script-heavy procedure that runs show it skipping, verifies each story four times, and runs the full suite repeatedly. Collapse the deterministic checks into one gate run and cut the layers that no measurement supports.

## Current State

- **The orchestrator procedure is too long, and runs show agents skipping it.** On the default path, `implement-story.md` calls 21 script subcommands and has 14 `unverifiable` carve-outs, 16 `DEGRADED` rules, three `review-override.py switch` toggles, a Jev shadow, and a 9-row first-match table at Gate 3. Phase 15 retro F6 shows lanes skipping steps ("I wrote the code myself instead of spawning a coding agent"; two stories sharing one Gate 3 review) while `exit-criteria.py` still returned `met`. Telling the lanes to "run the pipeline as written" did not stop it.
- **The same story is verified four times.** Each story gets the per-gate verifier scripts, the Gate 3 evaluator, `supervisor-agent`, and `exit-criteria.py`, and they re-derive overlapping claims. The supervisor caught F6 after the checker passed it (`.writ/eval/supervisor-trial/report.md`, n=1).
- **The full suite runs again and again (retro F21).** The coder, the reviewer and the lane each ran full gates: 3.2 h of lane 4's 4.6 h, and 18 full-suite runs by reviewers in lane 2. `implement-spec` Step 4.1 then runs it again.
- **Routing machinery to pick a reviewer.** Gate 0.5 (boundary map), Gate 2.5 (change surface plus crossings), the blast-radius check, the safety-fact switch, and the switch to the review agent after two failures all exist to choose between `evaluator-agent` and `review-agent` and to shape their inputs.
- **The file-creation rule forces over-prescription.** "Agents must only create files listed in the story's implementation tasks" (`implement-story.md:150`, `coding-agent.md:120`) makes specs plan the file layout in advance. This rule causes the related spec-tasks issue below.
- **Smaller cuts in `implement-spec.md`:**
  - Step 2.3's "task count × avg" estimate duplicates Step 2.3b and `/assess-spec`.
  - `.writ/context.md` is regenerated in both `implement-story` Step 4 and `implement-spec` Step 3.3.
  - `preflight.storyDepsValidated` and `postRun.contextRewritten` exist only so the checker can confirm afterwards that a step ran.
- **Gates are easy to add and hard to remove.** The removal trial (`2026-10-25-gate-upgrade-removal-measurement`) took a 1,446-line harness, 309 tests, 4 baseline stories and 6 findings labeled by the assistant, and removed nothing. Boundary map, change surface, drift-format, docs-check and app-verify have never been measured.

## Expected Outcome

- One `story-gate.py run` (name open) runs the deterministic checks and returns one verdict. The orchestrator handles only the judgment points: spawn the coder, spawn the reviewer, handle Large drift, escalate.
- Each fact is verified by one layer. Keep the supervisor and the scripts that catch real failures (`test-integrity.py`). Drop per-gate verifiers whose checks the supervisor or the checker repeats.
- Coder and reviewer run targeted tests only. The reviewer reads `recorded_test_results`. One full-suite run happens per spec, in `implement-spec` Step 4.1.
- One reviewer gets the diff and the acceptance criteria and scales its depth to the diff. Retire Gate 0.5, Gate 2.5 routing and the blast-radius routing unless a measurement shows they change verdicts.
- The file rule becomes: new files must be listed and justified in the coder's report, and review flags any that don't belong.
- Every gate, existing or new, carries a kill criterion (for example, "removed if it changes no verdict in N story runs"). Keeping a gate then needs evidence; removing one does not.
- Keep unchanged: `story-deps.py` validation, the end-of-spec integration suite, the coder + evaluator default, `test-integrity.py`, the supervisor, and the review-loop caps (most `reviewIterations` are 1; a few are 2–3).
- Validation: run the Phase 11 baseline stories before and after. Compare the exit-criteria pass rate, review findings, wall-clock time, and tokens per story. A shorter pipeline with more escaped defects is a regression.

## Relevant Files

- `commands/implement-story.md` - gates, scripts, routing, file-creation rule
- `commands/implement-spec.md` - supervisor step, Step 2.3, context regeneration, state provenance fields
- `agents/coding-agent.md` - file-creation limit (line 120), pre-report checks

## Related Issues

- [2026-11-06-spec-tasks-over-prescribe](2026-11-06-spec-tasks-over-prescribe.md) - same problem on the spec side; the file-creation rule links the two
- [2026-11-03-minimize-adversarial-review-surface](2026-11-03-minimize-adversarial-review-surface.md) - resolved review-surface audit; its evidence gate is one of the layers in scope here

## Notes

- Source: Phase 15 retro (`.writ/retros/2026-10-30-phase-15.md`) F6, F7, F8, F21, F26, and the execution records in `.writ/state/execution-*.json`.
- Retro findings F7, F8 and F26 propose adding rules to Gate 3 and the coding agent. Weigh each against this issue before applying it, or the pipeline grows again.

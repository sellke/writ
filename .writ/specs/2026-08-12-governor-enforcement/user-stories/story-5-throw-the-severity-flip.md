# Story 5: Throw the Severity Flip

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 4

## User Story

**As a** Writ maintainer whose four component-contract checks have been reporting into a channel nobody has to read
**I want to** the single constant `CONTRACT_CHECK_SEVERITY` set to `"structural"`, with every test that asserted the old posture inverted rather than deleted
**So that** a command that drops its contract fails the eval instead of adding a line to a report — and the seam `2026-08-11-governor-instrumentation` Story 7 built is used exactly as promised: one string, not four checks

## Acceptance Criteria

- [ ] Given Story 4's gate is **green**, when this story starts, then the flip proceeds. Given it is red, this story does not start (Business Rule 2).
- [ ] Given `scripts/eval-leanness.py` after this story, when the constant is read, then it is `CONTRACT_CHECK_SEVERITY = "structural"` and the trailing `# -> "structural"` marker is gone — a stale pending-action marker is the class `2026-08-11-retire-dead-prescription` exists to delete.
- [ ] Given the four contract check functions, when this story's diff is inspected, then **none of them changed**. The seam's entire claim is that the later spec changes the target, not the checks. `test_no_contract_check_touches_the_buckets_directly` must still pass.
- [ ] Given `FlipSeamTests.test_shipped_default_is_warnings`, when this story completes, then it has been **inverted** to assert the committed constant is `"structural"` — not deleted. It is the guard against an accidental un-flip, and deleting it removes the guard in the direction that now matters.
- [ ] Given `FlipSeamTests.test_default_routes_everything_non_blocking`, `.test_flip_moves_the_identical_dicts_to_structural`, `.test_main_exits_zero_and_stays_non_blocking_on_a_noncompliant_root`, and `EvalShBoundaryTests.test_shipped_severity_passes_the_gate_on_the_same_tree`, when this story completes, then each has been inverted to assert the post-flip posture and each passes.
- [ ] Given `test_the_constant_carries_its_handoff_comment`, when the constant's literal is changed to anything, then the test **fails** — it must anchor on the statement, not on the `-CONTRACT_CHECK_SEVERITY = "warnings"` line inside the handoff comment's diff preview, which survives the flip and makes the test silently inert.
- [ ] Given `EvalShBoundaryTests._run_leanness_check`, when it is asked for a severity, then the copy it writes genuinely carries that severity and the test **fails** if the substitution did not happen — its current `replace()` becomes a no-op post-flip and its `assertIn` passes trivially.
- [ ] Given `check_required_skills`'s findings, when the flip is live, then they are **still** in `warnings` — the `severity="warnings"` pin outlives the flip, per `system-instructions.md`'s graceful-degradation contract. `test_pinned_required_skills_findings_survive_the_flip` passes unchanged.
- [ ] Given `CONTRACT_CHECK_SEVERITY` set to an unrecognised value, when the checker runs, then findings still fall back to `warnings` and the process still exits 0. `test_unrecognised_severity_falls_back_to_warnings` passes unchanged.
- [ ] Given the absolute byte cap from Story 2, when `CONTRACT_CHECK_SEVERITY` is set to `"warnings"`, `"structural"`, or a typo, then the cap's findings are in `structural` in all three cases — the flip does not own the budget (Business Rule 3 of Story 2's design).
- [ ] Given the handoff comment at `scripts/eval-leanness.py:~262-277`, when a maintainer reads it cold, then it records the date the flip was thrown, the precondition Story 4 measured, the governing decisions (ADR-020 "Enforcement sequencing", ADR-021 reason 2), and what un-flipping would mean — the whole history at the constant, not scattered across a spec folder.
- [ ] Given the real repo after this story, when `bash scripts/eval.sh` runs, then it exits 0 — because the surface complies, which is what Story 4 proved.

## Implementation Tasks

- [ ] 5.1 Confirm Story 4's gate is green. If not, stop
- [ ] 5.2 Re-run the mutation inventory before editing: flip the constant in a scratch copy, run `python3 scripts/tests/test_eval_leanness_contract.py`, and record the exact failing set. The 2026-08-12 measurement was 81 tests / 5 failures; earlier stories may have changed it
- [ ] 5.3 Invert the five failing tests (see the table in Notes) — inverted, never deleted
- [ ] 5.4 Re-anchor `test_the_constant_carries_its_handoff_comment` on the assignment statement, and prove the re-anchor by breaking the constant and observing the failure
- [ ] 5.5 Re-anchor `EvalShBoundaryTests._run_leanness_check`'s substitution, and prove it by asserting the written copy differs from the committed source whenever the requested severity differs from the shipped one
- [ ] 5.6 Change the constant at `scripts/eval-leanness.py:278` and remove the trailing marker
- [ ] 5.7 Rewrite the handoff comment: date thrown, precondition verified, governing decisions, meaning of an un-flip
- [ ] 5.8 Verify no contract check function changed — `git diff` scoped to those functions must be empty
- [ ] 5.9 Raise `surfaces.scripts.justifications.{lines,chars}` for this story, dated, naming this story
- [ ] 5.10 Verify acceptance criteria: the full pytest file, `test_eval_leanness.sh`, all `scripts/tests/*.py`, and `bash scripts/eval.sh` end to end

## Notes

**Technical considerations:**

- **The one-line diff is the smallest part of this story.** The constant changes; five tests invert; two anchors get repaired; one comment gets rewritten. Instrumentation Story 7 promised the *checks* would not need editing, and that promise holds — the tests that asserted the pre-flip posture were always going to need inverting, and that is the seam working, not a leak in it.
- **Verified mutation inventory (2026-08-12).** A scratch copy with the constant flipped runs `scripts/tests/test_eval_leanness_contract.py` at **81 tests, 5 failures**:

  | Test | Post-flip form |
  |---|---|
  | `FlipSeamTests.test_shipped_default_is_warnings` | rename, assert `"structural"`, same "must not drift" intent |
  | `FlipSeamTests.test_default_routes_everything_non_blocking` | the default now routes everything blocking |
  | `FlipSeamTests.test_flip_moves_the_identical_dicts_to_structural` | reverse direction — pin `"warnings"` in-process, assert the identical dicts move back |
  | `FlipSeamTests.test_main_exits_zero_and_stays_non_blocking_on_a_noncompliant_root` | a non-compliant root now yields `structural`; the script **still exits 0** — `eval.sh` decides FAIL |
  | `EvalShBoundaryTests.test_shipped_severity_passes_the_gate_on_the_same_tree` | the shipped severity now FAILs the non-compliant tree; swap roles with `test_flipped_severity_fails_the_gate` |

- **The two tests that keep passing are the more dangerous finding.** Both anchor on the literal `CONTRACT_CHECK_SEVERITY = "warnings"`, which survives the flip inside the handoff comment's diff preview at `scripts/eval-leanness.py:276`. `test_the_constant_carries_its_handoff_comment` partitions on that literal and then inspects the preceding text — post-flip it inspects the comment and asserts nothing about the statement. `_run_leanness_check`'s `replace()` finds nothing and its `assertIn` passes trivially because the file already holds the requested value, so `test_flipped_severity_fails_the_gate` "passes" without having flipped anything. Instrumentation Story 7 documented this exact trap and defended one direction only. A red test announces itself; a silently inert test does not.
- **Inverting, not deleting, is the point.** `test_shipped_default_is_warnings` existed so a local experiment committed by accident could not turn the gate red unnoticed. The same test inverted stops a local experiment from turning the gate *off* unnoticed — which, now that the gate is real, is the failure that matters more.
- **The pinned and fallback behaviors are untouched.** `check_required_skills` stays `warnings` post-flip (`system-instructions.md` graceful degradation), and an unrecognised value still falls back to `warnings`. Both are instrumentation Business Rules and both survive this spec intact.

**Risks / challenges:**

- **Deleting the inconvenient tests.** Five red tests after a one-line change reads like the tests being wrong. They are not: each asserts a posture that was true and is now false, and each has a valid inverted form. Deleting any of them silently removes a guard.
- **A re-anchor that is itself untested.** Both repairs are string-matching fixes to string-matching tests, which is precisely where a fix can look right and assert nothing. Tasks 5.4 and 5.5 require *proving* each re-anchored test fails when its property is broken — not merely that it passes.
- **Leaking the flipped constant across tests.** Any in-process mutation without `addCleanup` contaminates every later test in the same process. `FlipSeamTests.setUp` already models the pattern.
- **A green `eval.sh` after the flip proves the surface complies, not that the gate works.** That proof is Story 6's, by mutation. Do not let a green run read as "enforcement verified."

**Integration points:**

- Hard-gated on Story 4. This is the sequencing the entire spec rests on.
- Does not touch Story 2's byte cap, which never routed through the seam and stays blocking regardless of this constant.
- Story 6 mutates real files and asserts the now-blocking checks FAIL naming each one.
- `scripts/eval-loop-bounds.py`'s `governor-boundary-intact` greps `eval-leanness.py` for the literal `check_loop_bounds`; nothing here renames it, and Story 6 asserts that rather than assuming it.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Business rules:** [Rule 2 (the flip is gated on measured compliance — this story is downstream of that gate); Rule 3 (the cap stays blocking regardless of this constant); Rule 4 (blocking findings name file and field)] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [The flip — the one-line diff, the five inverted tests, the two broken anchors, and the rewritten handoff comment] — from spec.md → ## Detailed Requirements → ### The flip
- **Error map rows:** [`CONTRACT_CHECK_SEVERITY` typo → falls back to `warnings`, and the cap stays blocking; the pre-flip gate test catches a drifted constant] — from sub-specs/technical-spec.md → ## Error & Rescue Map
- **Contract:** [Must include: "The flip is the **single named constant** `CONTRACT_CHECK_SEVERITY` … this spec changes one string, not four checks. Verify the seam still holds before using it."] — from spec.md → ## Contract (Locked)

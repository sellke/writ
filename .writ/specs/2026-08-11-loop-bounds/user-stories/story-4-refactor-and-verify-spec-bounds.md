# Story 4: Bounds on refactor and verify-spec

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** Story 1

## User Story

**As a** maintainer reading a bound that was set without evidence
**I want** `/refactor`'s and `/verify-spec`'s bounds to state plainly how thin their calibration is
**So that** a future reader does not infer precision that was never measured, and knows exactly which recorded run would justify changing the number

## Acceptance Criteria

- [ ] Given `commands/refactor.md`, when its frontmatter is read, then `loop.unit` is `change`, `loop.max_iterations` is `10`, `loop.on_exhaustion` is `halt_reported`, and `loop.calibrated_against` contains the literal phrase `no recorded run`, cites `commands/refactor.md:100`'s "7+ changes" splitting advisory as the sole anchor, and states the evidence quality as weak with an instruction to recalibrate after the first recorded run.
- [ ] Given `commands/verify-spec.md`, when its frontmatter is read, then `loop.unit` is `autofix_pass`, `loop.max_iterations` is `1`, `loop.on_exhaustion` is `halt_reported`, and `loop.calibrated_against` states that the command is single-pass by construction — Phase 3 checks → Phase 4 fixes → Phase 5 report, with no re-check step — so declaring 1 codifies existing behavior and can break no recorded run.
- [ ] Given `/refactor` reaches its bound mid-plan, when the loop terminates, then it reports the commits already landed, the remaining unexecuted changes, and a resume instruction — reusing the existing mid-plan-failure re-presentation at `refactor.md:124` rather than adding a second reporting path, and leaving the tree green.
- [ ] Given `/refactor`'s frontmatter, when it is inspected for a retry bound, then none exists — `skills/safe-refactor-loop/SKILL.md` reverts a red change immediately and never retries it, so a retry budget would contradict the skill.
- [ ] Given `/verify-spec` exhausts its single auto-fix pass, when the loop terminates, then the unresolved finding is reported in the existing Phase 5 verification report file and `/verify-spec` is named as the resume command — no new report artifact is introduced.
- [ ] Given `commands/verify-spec.md` is examined, when a re-check or re-verify step is searched for, then none exists — and this absence is asserted by a guard, so that adding one later forces the bound to be revisited rather than silently invalidated.

## Implementation Tasks

- [ ] 4.1 Confirm the zero-evidence claim for `/refactor` before writing its bound: search `.writ/state/` for any recorded `/refactor` execution and confirm there is none, and confirm `commands/refactor.md:100`'s "7+ changes" advisory is still the only quantitative anchor in the file
- [ ] 4.2 Confirm `/verify-spec`'s single-pass structure before writing its bound: verify that `commands/verify-spec.md` Phase 3 → Phase 4 → Phase 5 contains no re-check, re-run, or re-verify step (the only `again` is at line 698, describing `/release` invoking checks 1–8 through its own entry point, not a loop)
- [ ] 4.3 Append the `loop:` block to `commands/refactor.md`'s frontmatter, with `calibrated_against` carrying the literal `no recorded run` and the recalibration instruction
- [ ] 4.4 Append the `loop:` block to `commands/verify-spec.md`'s frontmatter, with `calibrated_against` stating "strong by construction" and explicitly noting that no `/verify-spec` runaway has ever been observed
- [ ] 4.5 Specify both `halt_reported` records against artifacts that already exist — `/refactor`'s Phase 4 completion report (commits landed, remaining plan) and `/verify-spec`'s Phase 5 verification report file — introducing no new artifact for either
- [ ] 4.6 Verify acceptance criteria are met, including the grep guard asserting `commands/verify-spec.md` still has no re-check step and the assertion that `refactor`'s `calibrated_against` contains `no recorded run`

## Notes

**Technical considerations:**

- **`/refactor`'s exhaustion is unusually cheap, and saying so is part of the deliverable.** `skills/safe-refactor-loop/SKILL.md` commits one green, single-concern, independently revertable commit per iteration, so the partial state at exhaustion is a clean commit series with a green tree — not a half-finished edit. That is why `halt_reported` is sufficient here and why 10 is a low-stakes number to be wrong about in the upward direction.
- **10 is above `refactor.md:100`'s existing 7+ advisory on purpose.** The bound must not fire before the advice that already exists; if it did, the file would give two different answers about the same plan size. 10 is a runaway guard, not a plan-size policy, and the frontmatter should say that.
- **`/verify-spec` is the honest weak point of the "0 of 5" measurement.** It has no runaway loop to bound; its auto-fix is a single linear pass. Including it is defensible as a *missing declaration*, but calling it a missing *bound* overstates the risk. `max_iterations: 1` is declared because the declaration is the deliverable and the number is free — not because a runaway was observed. Record that distinction in the file; do not smooth it over.
- `/verify-spec --product`'s Check P3 regeneration is the same single pass and needs no separate `nested` entry.

**Risks / challenges:**

- **`/refactor`'s bound is the one number in this spec most likely to be wrong.** Zero runs, one advisory sentence. The mitigation is not a better guess — it is the `no recorded run` literal in `calibrated_against` plus Story 5's assertion that the literal is present, so the weak evidence cannot be quietly upgraded to a confident-looking citation without an explicit edit.
- If someone later adds a re-check pass to `/verify-spec`, `max_iterations: 1` becomes wrong and would trip on the first legitimate two-pass run. The grep guard in task 4.6 is the tripwire for that, and it is the reason this story asserts an absence rather than trusting it.
- Adding a retry bound to `/refactor` would look like thoroughness and would contradict `safe-refactor-loop`. Resist it.

**Integration points:**

- Consumes Story 1's schema; adds no keys.
- Owns exactly two files: `commands/refactor.md` and `commands/verify-spec.md`. Stories 2 and 3 own disjoint sets and run in parallel.
- Reads `skills/safe-refactor-loop/SKILL.md` to confirm the no-retry property; modifies nothing there.
- Story 5 asserts the `no recorded run` literal and runs the `verify-spec` re-check guard.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Business rules:** [Rule 8 (a bound with thin evidence says so in the file — the primary rule this story implements; `/refactor` must carry the literal `no recorded run`), Rule 1 (every bound cites the run it was calibrated against, with evidence quality stated), Rule 3 (named, resumable state, never a bare halt)] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [The five bounds table — `refactor` (change/10/halt_reported, weak) and `verify-spec` (autofix_pass/1/halt_reported, strong by construction); The honest note on `/verify-spec`] — from spec.md → ## Detailed Requirements
- **Error map rows:** [`/refactor` mid-plan exhaustion reuses the existing re-presentation, tree stays green; adding a re-check step to `/verify-spec` invalidates the bound → grep guard catches it] — from sub-specs/technical-spec.md → Per-command application
- **Contract:** ["Each bound is derived from that loop's real semantics — `/verify-spec` bounds auto-fix passes — not a single global constant"; "be explicit where the evidence is thin — do not invent precision you do not have"] — from spec.md → ## Contract (Locked)

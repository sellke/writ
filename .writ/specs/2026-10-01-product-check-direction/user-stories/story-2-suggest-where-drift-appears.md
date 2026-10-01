# Story 2: Suggest the Check Where Drift Appears

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** Story 1

## User Story

**As a** Writ maintainer reading phase-completion and release-summary output to decide the next step
**I want to** see one line that points to `/verify-spec --product` at the two moments product docs fall behind
**So that** product-doc verification runs after implementation and its findings feed realignment, instead of the release summary jumping straight to `/plan-product --reconcile`

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.5

- [ ] Given `.writ/product/` exists, when `/implement-phase` renders its Step 4.2 completion report, then the line `Product docs may lag what shipped — run /verify-spec --product.` appears directly after the `Phase status:` line, and the template marks the line as omitted when `.writ/product/` is absent `[AC-2.1]`
- [ ] Given a release completes, when `commands/release.md`'s Phase 5 summary `- **Roadmap:**` bullet is rendered, then its pointer reads `run /verify-spec --product to check product docs against what shipped`, the old "consider `/plan-product --reconcile` if `mission-lite.md` needs a matching update" text is gone, and the summary carries no second product line `[AC-2.2]`
- [ ] Given `commands/release.md`'s roadmap-recording step, when its Boundary sentence and Derivative note are read, then the Boundary sentence names "`/verify-spec --product`'s P1/P4 checks, then `/plan-product --reconcile`" in that order, and the Derivative note points to `/verify-spec --product` as the command that regenerates `mission-lite.md` via Check P3 `[AC-2.3]`
- [ ] Given the edits grow `commands/implement-phase.md` and `commands/release.md`, when `uv run pytest` runs the governor byte ratchet, then both entries in `scripts/tests/test_governor_enforcement.py` are re-pinned to the new byte counts with a dated comment that discloses the growth and its reason, in the file's existing comment convention, and the suite passes `[AC-2.4]`
- [ ] Given `check_product_check_direction` in `scripts/eval.sh`, when the Story 2 `require_literal`/`forbid_literal` pins are added and each is broken by one deliberate mutation, then `bash scripts/eval.sh --check=product_check_direction` reports a finding for that mutation, and with the mutation reverted the full gate reports Findings 0 and the source issue ends with a `## Resolution` line carrying the date and commit `[AC-2.5]`

## Implementation Tasks

- [ ] 2.1 Add the three Story 2 pins to `check_product_check_direction` in `scripts/eval.sh` (`require_literal` `run /verify-spec --product` in `commands/implement-phase.md`; `require_literal` the new release pointer in `commands/release.md`; `forbid_literal` the old reconcile pointer in `commands/release.md`) and confirm they fail against today's files `[AC-2.1, AC-2.2, AC-2.5]`
- [ ] 2.2 Insert the conditional completion line after `Phase status:` in `commands/implement-phase.md` Step 4.2's report template, marked as shown only when `.writ/product/` exists `[AC-2.1]`
- [ ] 2.3 Replace the reconcile pointer on `commands/release.md`'s Phase 5 `- **Roadmap:**` bullet with the verification pointer (replace in place, no added line), then reorder the Boundary sentence and repoint the Derivative note in the roadmap-recording step `[AC-2.2, AC-2.3]`
- [ ] 2.4 Measure the new byte sizes and re-pin the `commands/implement-phase.md` and `commands/release.md` entries in `scripts/tests/test_governor_enforcement.py`, adding a dated comment that discloses the growth, matching the existing comment style in that ratchet block `[AC-2.4]`
- [ ] 2.5 Prove each pin bites: apply one mutation per pin (drop the implement-phase line, revert the release pointer, reinstate the old reconcile text), confirm `eval.sh --check=product_check_direction` reports it, and revert `[AC-2.5]`
- [ ] 2.6 Append `## Resolution` with the date and commit to `.writ/issues/improvements/2026-10-01-product-lint-misread-as-verify-spec.md` `[AC-2.5]`
- [ ] 2.7 Verify all criteria: `uv run pytest` passes, `bash scripts/eval.sh` reports Findings 0, and `rg -n "verify-spec --product" commands/implement-phase.md commands/release.md` shows exactly one completion-template line in each file `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`

## Notes

- **Depends on Story 1.** `check_product_check_direction` is created and registered in `scripts/eval.sh` by Story 1; this story only appends pins to it. If Story 1 hasn't landed, stop. Don't create a second check function.
- **Ratchet direction.** Both files are recorded violators under a one-way ratchet. Re-pinning upward is allowed here only because the growth is disclosed. Measure bytes after all edits, including the Boundary and Derivative rewording, so a single re-pin covers the whole story. Don't trim unrelated prose to dodge the re-pin.
- **Line numbers drift.** Release lines 397, 399, and 518 and ratchet lines 567–568 come from authoring time. Find each edit by its anchor text, not its line number.
- **Replace, don't stack.** The release summary must still have exactly one product-related pointer. The `forbid_literal` on the old text enforces this, so keep its string byte-exact to the current wording, backticks included.
- **No lint behavior change.** Checks P1–P4, their dispositions, and the product report path stay untouched. Only the pointers into them change.
- **Resolution timing.** The commit hash in `## Resolution` refers to this story's commit, so append it at commit time (or amend right after) to keep it accurate.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [] (technical-spec.md → Error & Rescue Map: not applicable)
- **Shadow paths:** [Happy path (summary points to `/verify-spec --product`), No `.writ/product/` (completion lines omitted)] from technical-spec.md → Shadow Paths
- **Business rules:** [Rule 1 One direction (verification may point to realignment), Rule 3 No behavior change to the lint, Rule 4 Conditional lines, Rule 5 Replace, don't stack] from spec.md → 📋 Business Rules
- **Experience:** [Happy path step 1 (completion summary suggests `/verify-spec --product`), Error experience (lines omitted without `.writ/product/`)] from spec.md → 🎯 Experience Design
- **Detailed requirements:** spec.md → Detailed Requirements → `commands/implement-phase.md` and `commands/release.md`
- **Pins and ratchet:** technical-spec.md → Eval Pins (Story 2) and the Files and Edits rows for `implement-phase.md`, `release.md`, `test_governor_enforcement.py`, and the source issue

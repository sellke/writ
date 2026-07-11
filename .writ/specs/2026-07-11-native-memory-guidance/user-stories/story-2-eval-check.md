# Story 2: `memory-interop` Eval Check + Registration

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1 + sibling `gbrain-compatibility-recipe` spec

## User Story

**As a** Writ maintainer who needs Phase 8's exit criteria machine-verified
**I want** one `memory-interop` eval check that asserts the adapter guidance and the GBrain recipe artifacts
**So that** "each adapter documents native memory vs. the ledger" and "the GBrain recipe exists with a round-trip guarantee" are green checks, not assertions

## Acceptance Criteria

- [ ] Given `scripts/eval.sh`, when `check_memory_interop` runs, then it asserts each adapter file contains the native-memory section and the two-place distinction (key phrases), modeled on `check_ralph_retirement` (`require_literal`), with no Python fixture.
- [ ] Given the same check, when it runs, then it asserts `skills/gbrain-interop/SKILL.md` exists, `gbrain-interop` is registered in `.writ/manifest.yaml` and root `SKILL.md`, and `.writ/docs/gbrain-recipe.md` exists with the round-trip guarantee and graceful-absence language.
- [ ] Given the same check, when it runs, then it `forbid_literal`s stale "persistent-database knowledge layer" framing on active surfaces (mission, README).
- [ ] Given `scripts/eval.sh`, when the check is registered, then exactly one `memory-interop` line is appended to the `CHECKS` array, no existing check is altered, and both `bash scripts/eval.sh --check=memory-interop` and the full `bash scripts/eval.sh` are green.

## Implementation Tasks

- [ ] 2.1 Add `check_memory_interop` to `scripts/eval.sh`, modeled on `check_ralph_retirement`: `require_literal` per adapter (native-memory section + two-place key phrases), `require_literal` on the sibling skill/recipe/registration, `forbid_literal` stale mission framing on active surfaces.
- [ ] 2.2 Append exactly one `memory-interop` entry to the `CHECKS` array (additive; do not reorder or edit existing entries).
- [ ] 2.3 Run `bash scripts/eval.sh --check=memory-interop` and fix findings until green.
- [ ] 2.4 Run the full `bash scripts/eval.sh`; confirm 0 findings and 0 run errors on the phase branch.

## Notes

- This spec is the single writer of `scripts/eval.sh` in Phase 8; the sibling spec deliberately does not touch it, so the isolated lanes never collide.
- If a sibling-artifact assertion fails, the run order is wrong — fix the order, never weaken the assertion.
- Keep the check deterministic and file-scoped; no network, no fixture harness.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] `scripts/eval.sh --check=memory-interop` green; full suite green (0 findings, 0 run errors)
- [ ] Code reviewed

## Context for Agents

- **Business rules:** [`spec.md` → `### Business Rules` → Rules 6 (single-writer), 7 (asserts both specs), 8 (docs only)]
- **Design:** [`sub-specs/technical-spec.md` → `### D4` (documentation check), `### D5` (single-writer discipline)]
- **Model:** [`scripts/eval.sh` → `check_ralph_retirement`]
- **Error paths:** [`sub-specs/technical-spec.md` → `## Error & Rescue Map`]

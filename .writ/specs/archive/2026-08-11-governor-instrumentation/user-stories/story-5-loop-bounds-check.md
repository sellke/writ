# Story 5: Loop Bounds Declaration Check

> **Status:** Complete
> **Priority:** High
> **Dependencies:** Story 2, Story 3

## User Story

**As a** Writ maintainer running an autonomous `/implement-phase`
**I want to** `eval-leanness.py` to assert that each of the five loop-bearing commands declares `loop.max_iterations` and `loop.on_exhaustion`
**So that** the phase's highest-severity measured gap — **0 of 5** loop-bearing commands declaring any iteration bound — is visible on every eval run instead of only in a roadmap table

## Acceptance Criteria

- [x] Given a fixture `implement-story.md` declaring both `loop.max_iterations` and `loop.on_exhaustion`, when the check runs, then it emits zero findings for that file.
- [x] Given a fixture loop-bearing command declaring `loop.max_iterations` but not `loop.on_exhaustion`, when the check runs, then it emits exactly one finding naming the file and the missing field — a bound with no exhaustion behavior is half a contract, and the finding says which half.
- [x] Given a fixture loop-bearing command declaring a `loop:` key with no children, when the check runs, then it emits two findings (one per missing field), not one aggregate `loop:` finding.
- [x] Given a command that is **not** in the five-command list (e.g. `commands/status.md`), when the check runs, then it is never checked and never produces a finding — the population is the named constant, not an inference from file contents.
- [x] Given the constant names a command whose file does not exist on disk, when the check runs, then it emits a finding for that name (`commands/<name>.md → missing`), so the constant cannot silently rot the way an unsynced list would.
- [x] Given the real repo after this story, when `eval-leanness.py` runs, then this check's findings all land in `warnings`, `structural` remains `[]`, and `eval.sh` exits 0.

> **Measured correction, 2026-08-11 (implementation).** The spec's **10** was measured before `2026-08-11-loop-bounds` landed. All five loop-bearing commands now declare `loop:` with `unit` / `max_iterations` / `on_exhaustion` / `calibrated_against`, so this check contributes **0** findings and `contract_compliance` reports `loop_commands_bounded: 5` of `loop_commands_checked: 5`. The count is asserted against fixture trees; behaviour is asserted against the real repo.
>
> **Task 5.1 outcome (field shape, re-read as required).** `2026-08-11-loop-bounds` shipped exactly the names this check expected — `max_iterations` and `on_exhaustion` at the top level of `loop:`, with an optional `nested:` sub-map. No divergence to record.
>
> **Task 5.3 amendment.** The five-command population is **cross-read** from `scripts/eval-loop-bounds.py`'s own `LOOP_BEARING_COMMANDS` (parsed with `ast`, never imported), not restated. That checker landed first and its docstring declares itself *"the enforcement point when a sixth command acquires a loop"*. Two hand-maintained copies of one population would drift, and a drifted presence/correctness split reports a file twice or not at all — the duplicate-signal noise Business Rule 2 exists to prevent. A module-level literal remains as the fallback for a tree where the sibling is absent or unparseable, and a test asserts the two agree.
- [x] Given `metrics.contract_compliance` after this story, when it is read, then it reports `loop_commands_checked` and `loop_commands_bounded` as counts.

## Implementation Tasks

- [x] 5.1 Re-read `2026-08-11-loop-bounds`'s field shape before writing anything. As authored it names `loop.max_iterations` / `loop.on_exhaustion`, required at the top level of `loop:`, with an optional `nested:` sub-map used only by `implement-story` — this matches Check 3's expectation. If it has since changed, adopt that spec's names and record the divergence in this spec's drift log; never invent a competing convention
- [x] 5.2 Write tests in `scripts/tests/test_eval_leanness_contract.py`: both fields present, one field missing, `loop:` with no children, a non-listed command ignored, a listed command missing from disk, and a nested-vs-flattened field shape
- [x] 5.3 Add `LOOP_BEARING_COMMANDS` as a module-level constant with the comment explaining why the list is fixed rather than inferred (inferring "does this command loop?" from prose needs a keyword grammar per variant — the fragility ADR-020 rejects) and citing the roadmap measurement that produced it
- [x] 5.4 Add `check_loop_bounds(root)` — pure function, per-file-per-field findings, accepting either a nested `loop:` block or flattened keys, reusing Story 3's `read_frontmatter()`
- [x] 5.5 Wire the check into `main()` through Story 3's router; add `loop_commands_checked` / `loop_commands_bounded` to `metrics.contract_compliance`
- [x] 5.6 Verify acceptance criteria against the real repo (10 findings, all in `warnings`, exit 0) and verify all tests pass — new pytest cases, `test_eval_leanness.sh`, full `scripts/tests/*.py` suite, `bash scripts/eval.sh --check=leanness`

## Notes

**Technical considerations:**

- **The five are named, not inferred.** `implement-phase`, `implement-spec`, `implement-story`, `refactor`, `verify-spec` — the population the roadmap's Phase 10 problem table measured as *"Loop-bearing commands declaring an iteration bound: 0 of 5."* Inferring loop-bearing-ness from file contents means a keyword grammar (`loop`, `iterate`, `retry`, `until`, `each`) with a false-positive rate that would produce findings against commands that merely *mention* iteration. A hand-maintained constant with a comment is the honest instrument.
- **The list can rot, so the check watches itself.** A named command missing from disk is a finding. This is the guard `GATE_AGENT_FILES` in the same module lacks — its own comment admits it is *"kept in sync by hand"* and silently understates a metric when a gate is added and not mirrored. Do not repeat that pattern.
- **Field shape is a downstream decision.** `loop.max_iterations` / `loop.on_exhaustion` is this spec's stated expectation; `2026-08-11-loop-bounds` owns the final form. The presence test accepting either a nested `loop:` block or flattened `loop.max_iterations:` keys is deliberate slack for that reason — but slack in the *reader*, not ambiguity in the *contract*. Once the dependency spec picks a shape, the finding text should name that exact shape.
- Existing evidence that the bounds already exist as prose, unenforced: `implement-story.md` documents `MAX_SELF_FIX_ITERATIONS = 3`, a 3-iteration review loop, and a separate 2-iteration testing cap — all in prose, none machine-readable. The declaration this check asserts is not new policy; it is the same policy in a checkable carrier.

**Risks / challenges:**

- **This is the one story a dependency spec can force to rework.** If `2026-08-11-loop-bounds` names the fields differently, task 5.1 catches it before implementation; if it lands *after* this story, the rework is bounded to one constant, one function, and its tests. Nothing else in this spec is affected.
- `verify-spec` is the least obviously loop-bearing of the five — its iteration is the `--all` multi-spec pass and the auto-fix/re-verify cycle rather than a retry loop, and `grep -i 'loop\|iteration\|retry'` over `commands/verify-spec.md` returns nothing. `2026-08-11-loop-bounds` reaches the same conclusion and keeps it on the list anyway, declaring `max_iterations: 1` on the stated grounds that *"the declaration is the deliverable and the number is free — not because a real `/verify-spec` runaway has ever been observed."* Check 3 keeps it for the same reason: it asserts declaration, never runaway risk. Do not quietly drop it, and do not overstate what its presence proves.

**Integration points:**

- Consumes Story 3's `read_frontmatter()` and `emit_contract_findings()`. Adds no parsing or routing.
- Independent of Stories 4 and 6 — parallel after Story 3.
- Story 7 asserts this check's findings move to `structural` when the constant flips.
- Real remediation (adding the declarations to the five files) belongs to `2026-08-11-loop-bounds`, which per the roadmap wires them to `phase-state.py`'s existing `retry` / `quarantine` paths. This story asserts declaration only; it neither reads nor enforces the declared values.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Business rules:** [Rule 2 (every finding names the exact file and field — including which half of the loop contract is missing); Rule 4 (checks read the surface, never modify it — the declarations themselves belong to `2026-08-11-loop-bounds`)] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [Check 3 — loop bounds: the five named commands, the fixed-list rationale, the deference to `2026-08-11-loop-bounds` on field shape] — from spec.md → ## Detailed Requirements → ### Check 3
- **Error map rows:** [`LOOP_BEARING_COMMANDS` resolution → a named command missing from disk is a finding so the constant cannot rot silently; `loop:` present with no children → 2 findings] — from sub-specs/technical-spec.md → ## Error & Rescue Map, ## Shadow Paths
- **Contract:** [Technical Concerns: "Check 3 depends on a field shape this spec does not own … If that spec picks different names, Check 3 changes its constant and its tests; the seam, the router, and the other three checks are unaffected."] — from spec.md → ## Technical Concerns

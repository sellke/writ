# Story 7: Warnings→Structural Flip Seam

> **Status:** Complete
> **Priority:** High
> **Dependencies:** Story 3, Story 4, Story 5, Story 6

## User Story

**As a** Writ maintainer who will later run the `governor-enforcement` spec
**I want to** proof — from a test that actually throws the switch — that flipping one named constant turns every contract finding blocking without editing a single check
**So that** "flip it later" is a verified property of this code rather than a promise in a spec that the next implementer has to re-derive

## Acceptance Criteria

- [x] Given `CONTRACT_CHECK_SEVERITY` is `"warnings"` (the shipped default), when the checker runs against a non-compliant fixture, then every contract finding is in `warnings`, `structural` is `[]`, and the process exits 0.
- [x] Given the same fixture and the same run, when `CONTRACT_CHECK_SEVERITY` is set to `"structural"` in-process, then the **identical finding dicts** — same `subject`, `what`, and `fix` values, same count — appear in `structural` and none remain in `warnings`.
- [x] Given the flip, when `check_required_skills`'s findings are inspected, then they are **still** in `warnings` — the `severity="warnings"` pin survives the flip, per `system-instructions.md`'s graceful-degradation contract (Business Rule 6).
- [x] Given `CONTRACT_CHECK_SEVERITY` is set to an unrecognized value (e.g. `"blocking"`, a plausible typo in the later spec's diff), when the checker runs, then findings fall back to `warnings` and the process exits 0 — a typo must never silently disable a check nor accidentally block CI.
- [x] Given the flip is applied and `eval.sh`'s leanness check runs, when the contract findings land in `structural`, then `eval.sh` reports FAIL for that check — proving the seam reaches all the way to the gate, not just to the JSON.

> **Task 7.5 outcome, 2026-08-11.** The end-to-end proof was achievable and no coverage reduction needs recording. `EvalShBoundaryTests` builds a temp project root, copies `eval.sh` and a **copy** of `eval-leanness.py` with the constant flipped into its `scripts/`, and runs `bash eval.sh --check=leanness` for real: exit 1 and `FAIL` in the report when flipped, exit 0 and `PASS` when shipped, on the identical tree. The committed script is never mutated. The same flipped run also proves the pin reaches the gate — `required_skills:` is still rendered as a non-blocking `WARNING` note in a FAILing report.
>
> **A trap the run caught.** A naive `replace('CONTRACT_CHECK_SEVERITY = "warnings"', ...)` rewrites the *diff preview inside the handoff comment* rather than the statement, and the flipped copy behaves exactly like the shipped one. The test anchors on the leading newline. Worth knowing before the `governor-enforcement` spec automates its own one-line change.
- [x] Given `scripts/eval-leanness.py` after this story, when the four contract check functions are inspected programmatically, then none of them references `structural` or `warnings` — every one returns a `list[dict]` and routing happens only in `emit_contract_findings()`. This is asserted by a test, not by review.
- [x] Given a maintainer reading `scripts/eval-leanness.py` cold, when they reach `CONTRACT_CHECK_SEVERITY`, then the comment names the flipping spec (`governor-enforcement`), the precondition (the migration specs reaching compliance), and the governing decision (ADR-020 "Enforcement sequencing (load-bearing)") — the whole handoff is at the constant, not scattered across a spec folder.
- [x] Given the flip test exists, when `CONTRACT_CHECK_SEVERITY` is left flipped by accident in a working tree, then the test suite fails loudly — the default value is itself asserted, so the shipped state cannot drift to blocking unnoticed.

## Implementation Tasks

- [x] 7.1 Write the flip test in `scripts/tests/test_eval_leanness_contract.py`: load `eval-leanness.py` by path, build one non-compliant fixture tree exercising all four checks, capture findings at `"warnings"`, set `module.CONTRACT_CHECK_SEVERITY = "structural"`, re-run, and assert dict-for-dict equality of the moved findings
- [x] 7.2 Add the pinned-check assertion: after the flip, `required_skills:` findings remain in `warnings` while the other three checks' findings do not
- [x] 7.3 Add the unrecognized-value fallback test (`"blocking"` → `warnings`, exit 0) and the shipped-default test (`CONTRACT_CHECK_SEVERITY == "warnings"` as committed)
- [x] 7.4 Add the source-level assertion that no contract check function touches `structural` / `warnings` directly — inspect the functions' source via `inspect.getsource()` rather than grepping the file, so a rename cannot bypass it
- [x] 7.5 Add the `eval.sh`-boundary scenario proving a `structural` finding actually FAILs the leanness check — a temp-copy or fixture-root run, never a mutation of the committed script
- [x] 7.6 Write the handoff comment at `CONTRACT_CHECK_SEVERITY`: which spec flips it, what must be true first, which ADR governs, and the one-line diff it becomes
- [x] 7.7 Verify acceptance criteria and that the full suite passes — new pytest file, `test_eval_leanness.sh`, all `scripts/tests/*.py`, and `bash scripts/eval.sh` end-to-end with the constant at its shipped `"warnings"` default

## Notes

**Technical considerations:**

- **This story does not build the seam; it throws it.** Story 3 introduces `CONTRACT_CHECK_SEVERITY` and `emit_contract_findings()` because the first check needs somewhere to route. This story is the proof that the mechanism is genuinely single-point — which cannot be demonstrated until findings exist from every check to move.
- **Dict-for-dict equality is the assertion that matters.** "Findings appear in `structural`" is weak; a check could legitimately produce *different* text in blocking mode and still pass that. Business Rule 3 requires the identical findings move, because the whole claim is that the later spec changes the *target*, not the *checks*. Compare the full dicts.
- **In-process mutation is the right test mechanism.** `importlib.util.spec_from_file_location` is the established recipe in this repo for hyphenated script filenames (`test_archive_sweep.py`, `test_spec_status.py`, `test_story_deps.py`), and it makes `module.CONTRACT_CHECK_SEVERITY = "structural"` a one-line setup. Do not test the flip by rewriting the committed script, and do not add a CLI flag or env var to make flipping easier — a runtime switch would let `eval.sh`, CI, and a local run disagree about whether the gate binds, which is precisely the property a committed one-line diff guarantees.
- **The unrecognized-value fallback is not defensive padding.** The later spec's entire change is one string literal. A typo there is the single most likely failure mode, and both wrong outcomes are bad: silently non-blocking (the gate quietly stops mattering) or accidentally blocking on a value nobody reviewed. Falling back to `warnings` is the safe half; the test is what makes it a decision instead of an accident.
- **The shipped-default assertion guards the other direction.** Someone experimenting with the flip locally and committing it would turn `eval.sh` red on ~142 findings — the exact "permanently red gate becomes invisible" outcome ADR-020 warns about. Asserting the committed value catches it in CI.

**Risks / challenges:**

- **`eval.sh`-boundary testing is the awkward task.** `check_leanness()` invokes `eval-leanness.py` as a subprocess against `$PROJECT_ROOT`, so exercising the FAIL path means either a fixture root or a temp copy of the script with the constant flipped. Prefer a temp copy plus a fixture root; never mutate the committed script mid-test. If this proves genuinely infeasible in the shell harness, assert the `eval.sh` contract at the JSON boundary (a non-empty `structural` array maps to `add_finding`) and record the reduced coverage honestly in the drift log rather than claiming the end-to-end proof.
- **A passing flip test on fixtures says nothing about the 142 real findings.** The seam is proven mechanically here; whether the surface is *ready* to be flipped is the `governor-enforcement` spec's gate, and it depends on the two migration specs completing. Do not let a green flip test read as "ready to enforce."

**Integration points:**

- Depends on all four checks existing (Stories 3–6) — the flip test asserts behavior across every one, including Story 6's exception.
- Produces the handoff artifact for the future `governor-enforcement` spec: a named constant, a documented precondition, and a test that already covers the post-flip state. That spec's change should be one line plus a baseline of expectations, not an investigation.
- Touches no command, agent, or skill file. The surface stays exactly as non-compliant after this story as before it — by design (Business Rule 4).

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Business rules:** [Rule 3 (the flip is one named constant and one emission router, verified by a test that flips it and observes findings become blocking — this story *is* Rule 3); Rule 6 (`required_skills:` stays non-blocking after the flip); Rule 4 (checks read the surface, never modify it)] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [Emission seam — the constant, the router, the `main()` wiring, and the explicit-override path used by `required_skills:`] — from spec.md → ## Detailed Requirements → ### Emission seam
- **Error map rows:** [Severity flip → an unrecognized value falls back to `warnings`; a typo must never silently disable a check nor accidentally block CI] — from sub-specs/technical-spec.md → ## Error & Rescue Map
- **Contract:** [Must include: "They must be written so the later `governor-enforcement` spec flips them to `structural` by changing the emission target, not by rewriting the checks."; Out of Scope: "Flipping `CONTRACT_CHECK_SEVERITY` to `\"structural\"` … is the later spec's single-line change."] — from spec.md → ## Contract (Locked), ## Out of Scope

# Story 4: `## Completion` Presence Check

> **Status:** Complete
> **Priority:** High
> **Dependencies:** Story 2, Story 3

## User Story

**As a** Writ maintainer whose commands carry `## Completion` only by emergent convention — 13 of 32, never mandated, never checked
**I want to** `eval-leanness.py` to name every command file that violates that mandate
**So that** a template rule that 18 of 31 commands ignore stops being enforced by nobody

## Acceptance Criteria

- [x] Given a fixture command containing a line matching `^## Completion$`, when the check runs, then it emits zero findings for that file.
- [x] Given a fixture command with no `## Completion` heading, when the check runs, then it emits exactly one finding whose `subject` names the file and the section (e.g. `commands/create-spec.md → ## Completion`).
- [x] Given a fixture command whose heading is `## Completion Criteria` or `### Completion`, when the check runs, then it emits a finding, and the finding's `fix` text states the exact required spelling so the near-miss is diagnosable rather than mysterious.
- [x] Given a fixture command with a `## Completion` heading and no body under it, when the check runs, then it emits zero findings — this check asserts presence, not content, and must not silently expand its own scope.
- [x] Given `commands/_preamble.md`, when the check runs, then it is never checked (existing `is_infra()` rule, no hardcoded filename).
- [x] Given the real repo after this story, when `eval-leanness.py` runs, then this check's findings all land in `warnings`, `structural` remains `[]`, and `eval.sh` exits 0.

> **Measured correction, 2026-08-11 (implementation).** The spec's **18** was measured before `2026-08-11-component-contract` landed; that spec added `## Completion` to every command it was missing from. All 31 checkable commands now carry it, so this check contributes **0** findings and `contract_compliance.commands_with_completion` reads `31`. This is precisely the moving-surface hazard this story's own risk note names: the **count** is asserted against fixture trees (compliant, missing, `## Completion Criteria`, `### Completion`, heading-with-empty-body, heading-only-inside-a-fence, `_preamble.md`, absent directory) and *behaviour* against the real repo.
- [x] Given `metrics.contract_compliance` after this story, when it is read, then it reports `commands_with_completion` as a count.
- [x] Given `scripts/eval-leanness.py` after this story, when the new check is inspected, then it returns a `list[dict]`, routes through `emit_contract_findings()`, and introduces no parsing or routing mechanism of its own.

## Implementation Tasks

- [x] 4.1 Write tests in `scripts/tests/test_eval_leanness_contract.py`: compliant command, missing heading, `## Completion Criteria` near-miss, `### Completion` near-miss, heading-with-empty-body, `_preamble.md` exclusion, absent `commands/` directory
- [x] 4.2 Add `check_completion_sections(root)` — exact `^## Completion\s*$` match per non-infra command, reusing `all_command_files()` / `is_infra()`
- [x] 4.3 Write the finding text so `fix` names the exact required H2 spelling and cites `commands/new-command.md` as the mandate's source
- [x] 4.4 Wire the check into `main()` through Story 3's router; add `commands_with_completion` to `metrics.contract_compliance`
- [x] 4.5 Verify acceptance criteria against the real repo: exactly 18 findings, all in `warnings`, exit 0, and the 13 compliant files produce none
- [x] 4.6 Verify all tests pass — new pytest cases, `test_eval_leanness.sh`, full `scripts/tests/*.py` suite, and `bash scripts/eval.sh --check=leanness`

## Notes

**Technical considerations:**

- **Verified counts.** `grep -l '^## Completion' commands/*.md` returns 13 of 32 files; `commands/_preamble.md` is *not* among them and is excluded as infra, so the checkable population is 31 and the expected finding count is 18. ADR-020 and the roadmap both report "13 of 32" — the same measurement, counted against the raw file list rather than the non-infra list. Do not "correct" either number; state which population each refers to.
- **The near-miss `fix` text is load-bearing.** `## Completion Criteria` is the likeliest wrong guess, and a maintainer who writes it, sees the finding persist, and cannot tell why is one step from ignoring the channel entirely — the failure mode this whole spec is built to avoid. Name the exact spelling.
- **Presence, not content.** A `## Completion` heading with nothing under it passes. Asserting the section is *useful* requires judging prose, which is exactly what ADR-020 rejects for `## Goal`-style headings. Scope creep here would be a real defect, not a bonus.
- Exact-match on the H2 is deliberate. A tolerant matcher (`startswith("## Completion")`) would accept `## Completion Criteria`, which defeats the point of having one canonical section name that `/verify-spec` and `/refresh-command` can later key off.

**Risks / challenges:**

- Fenced code blocks in command files can contain `## Completion` as example markdown. Decide explicitly whether to skip fenced regions; the simplest correct answer is to skip them, matching `readme_command_names()`'s existing fence-tracking in the same module. Test with a fixture that has the heading *only* inside a fence.
- The finding count is a hard assertion against a moving surface: if a concurrent spec adds `## Completion` to a command, this story's "exactly 18" criterion changes. Assert the count from a fixture tree, and assert *behavior* (the 13 known-compliant files produce no finding) against the real repo.

**Integration points:**

- Consumes Story 3's `emit_contract_findings()` router and `is_infra()` reuse pattern. Adds nothing to the seam.
- Independent of Stories 5 and 6 — different check function, different fixture tree, no shared state. All three can run in parallel after Story 3.
- Story 7 asserts this check's findings move to `structural` when the constant flips.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Business rules:** [Rule 2 (every finding names the exact file and section); Rule 4 (checks read the surface, never modify it — this story adds no `## Completion` section to any command); Rule 7 (`_preamble.md` excluded via `is_infra()`)] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [Check 2 — `## Completion` presence: exact H2 match, 18 expected findings, near-miss `fix` text] — from spec.md → ## Detailed Requirements → ### Check 2
- **Error map rows:** [`## Completion` shadow-path row: heading-only section → 0 findings (presence, not content); unreadable file → skipped with the existing warning, run continues; missing `commands/` → 0 findings] — from sub-specs/technical-spec.md → ## Shadow Paths, ## Error & Rescue Map
- **Contract:** [Deliverable: "New structural checks in `scripts/eval-leanness.py` — contract presence, `## Completion` presence, loop bounds, and `required_skills:` resolution — landing as non-blocking `warnings`"] — from spec.md → ## Contract (Locked)

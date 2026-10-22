# Story 3: Verification-Record Tests, prototype.md Reconciliation, and Issue Note

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** Story 1, Story 2

## User Story

**As a** maintainer **I want to** have the test suite fail when a verification record loses its status mark or its `https://` source, and to reconcile `/prototype` Step 2.5 with the recorded observations **So that** the records stay honest after this spec closes and the UAT reviewer can trust each dated status.

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.5

- [x] Given the four adapter files (`cursor`, `claude-code`, `codex`, `openclaw`) each hold a `#### Verification record — YYYY-MM-DD` heading, when `uv run --python 3.9 pytest` runs, then `test_verification_records[<adapter>]` passes for all four, and fails for any adapter whose record heading is absent or whose first table has no data row. `[AC-3.1]`
- [x] Given a verification record row, when the test reads its Status and Source cells, then Status matches `^(verified|unverified) \d{4}-\d{2}-\d{2}( \((pending UAT|no deployment)\))?$` and Source starts with `https://`; a row with Source `not documented` or a Status without a date fails, and the assertion message names the adapter. `[AC-3.2]`
- [x] Given Stories 1 and 2 have written their records, when `uv run --python 3.9 pytest`, `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`, and `bash scripts/eval.sh` run outside any sandbox, then all three pass with no FAIL lines and 0 eval findings, and `test_adapter_canvas_row` and `test_prototype_names_capability` pass. `[AC-3.3]`
- [x] Given `commands/prototype.md` Step 2.5 "Render through the platform" and the four records, when a recorded observation contradicts a row, then only that row changes and `drift-log.md` gets one `DEV-NNN` entry for it; when no observation contradicts a row, then `commands/prototype.md` is unchanged and `drift-log.md` gets no entry. `[AC-3.4]`
- [x] Given the origin issue `.writ/issues/bugs/2026-10-19-prototype-visual-preview-cursor-only.md`, when this story closes, then it ends with a `### Verification` section under `## Resolution` that names `2026-10-22-rendering-delegation-rows` and each adapter's status as recorded at spec close, and `test_issue_resolution` still passes. `[AC-3.5]`

## Implementation Tasks

- [x] 3.1 Write the failing test first: in `scripts/tests/test_platform_neutral_names.py`, confirm `test_verification_records` (added by Story 1, extended by Story 2) is parametrized over `cursor`, `claude-code`, `codex`, and `openclaw`, then factor its checks into a helper and add one negative case that feeds an inline record with Source `not documented` and a Status without a date and confirms the helper rejects both `[AC-3.1, AC-3.2]`
- [x] 3.2 Make each assertion message name the adapter and the failing cell, for example `cursor: Status "verified" does not match the status grammar`. `[AC-3.2]`
- [x] 3.3 Run `uv run --python 3.9 pytest` and confirm `test_verification_records[*]` passes against the Story 1 and Story 2 records. If Story 1 or Story 2 changed a word that `test_adapter_canvas_row` pins and did not update the keyword list, update it now; otherwise leave the test unchanged `[AC-3.1, AC-3.3]`
- [x] 3.4 Reconcile `commands/prototype.md` Step 2.5 against the four records. Change a row only where a recorded observation contradicts it. For each change, add one `DEV-NNN` entry to `.writ/specs/2026-10-22-rendering-delegation-rows/drift-log.md` (create the file if absent) and update `test_prototype_names_capability` in the same commit if a label changed. If no observation contradicts a row, leave `commands/prototype.md` untouched. `[AC-3.4]`
- [x] 3.5 Append `### Verification` under `## Resolution` in `.writ/issues/bugs/2026-10-19-prototype-visual-preview-cursor-only.md`. Name `2026-10-22-rendering-delegation-rows` and each adapter's status from its record at spec close. Confirm `test_issue_resolution` still passes. `[AC-3.5]`
- [x] 3.6 Run `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done` and confirm no `FAIL` line prints. `[AC-3.3]`
- [x] 3.7 Run `bash scripts/eval.sh` outside any sandbox and confirm 0 findings. Run `uv run --python 3.9 pytest` again on the final tree. `[AC-3.3]`

## Notes

**Technical considerations**
- Helpers `read`, `section`, `first_table`, and `cells` live in `scripts/tests/test_platform_neutral_names.py`. Python 3.9 stdlib only. No network: URLs get a prefix check only.
- The Status pattern is the full grammar from `technical-spec.md` § Verification Record Format, including the optional reason. Business Rule 1 names the same two status values.
- `test_prototype_names_capability` pins Step 2.5's three labels in order: "Native artboard/design surface", `` `canvas-preview` `` (the adapter maps it), and "Neither". Row text can change without breaking it. A label change breaks it.
- The test checks format, not truth. A `verified` status that the UAT run never produced passes the test. Review has to catch it.

**Risks**
- A record with a non-`https://` Source (for example, "not documented") fails. Fix it by citing the docs index page and writing "not documented" in the Observed cell (spec-lite, Nil input).
- Two record headings in one adapter: the test reads the first one. Keep one per adapter.
- A `verified` status with no version in the Platform cell passes the grammar. Flag it in review.
- `test_issue_resolution` (`ISSUE_RESOLUTIONS` in the same test file) requires `## Resolution` to be the last `#` or `##` heading in the origin issue. A `## Verification` after it fails that test. This story writes `### Verification` under `## Resolution`, which matches the spec's "under its ## Resolution" and keeps the test green. Keep the "2026-10-21", spec slug, and lane branch lines in Resolution. The test checks for them.
- Drift-log labels: existing drift logs (for example `.writ/specs/2026-10-20-ci-and-update-integrity/drift-log.md`) use "Spec said / Implementation did / Reason / Resolution". Use those labels, not "Reality".

**Technical references:** technical-spec.md → ## Tests (Story 3), ## Verification Record Format.

**Integration points**
- Story 1 writes the `claude-code` record. Story 2 writes the `cursor`, `codex`, and `openclaw` records and the UAT protocols. Story 3 reads the records. A malformed record goes back to the story that wrote it.
- `2026-10-22-generated-platform-trees` parses adapter tables by heading. Add no table to any adapter.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** []
- **Shadow paths:** `technical-spec.md → ## Shadow Paths` (Nil input, Empty input)
- **Business rules:** `spec.md → ## Business Rules (Expanded)` (Rule 1 record shape, Rule 7 prototype.md read-only unless contradicted, Rule 8 tests, Rule 9 issue note)
- **Experience:** `spec.md → ## Experience Design → ### State Catalog` (Maintainer removes a status mark or URL from a record)

## What Was Built

**Implementation Date:** 2026-10-22

### Files Created

None.

### Files Modified

- **`scripts/tests/test_platform_neutral_names.py`** — the record assertions moved from `test_verification_records` into `check_record(adapter, table)` (five columns, at least one data row, five cells per row, anchored Status grammar, `https://` Source; every message names the adapter and the failing cell); `test_verification_records` keeps the heading lookup and calls the helper for all four adapters. New `test_check_record_rejects_bad_cells` feeds inline rows with Source `not documented`, a Status without a date, and a Status with a version appended, and a header with no data row, asserting each message. New `test_prototype_render_table_reconciled` (Step 2.5 labels unchanged, no vendor tool, no Step 2.5 DEV entry in this spec's drift log) and `test_issue_verification_note` (the issue's `### Verification` under `## Resolution` names the spec and each adapter's recorded status).
- **`.writ/issues/bugs/2026-10-19-prototype-visual-preview-cursor-only.md`** — `### Verification` appended inside `## Resolution`: the spec, the Phase 14 lane, and the status of each adapter at spec close (claude-code verified; cursor and codex unverified, pending UAT; openclaw unverified, no deployment), with the protocol location and the note that `commands/prototype.md` Step 2.5 is unchanged.

### Implementation Decisions

1. **`commands/prototype.md` untouched, no drift entry** — Business Rule 7's trigger did not fire: Claude Code's record shows the Claude Design type listable from inside a command run, so the "Native artboard/design surface" row stands; Cursor's canvas is documented but unverified; Codex and OpenClaw document no native surface, and the table's rows are conditional on availability. `test_prototype_names_capability` is unchanged.
2. **Negative test on the helper, not on a temp file** — `check_record` takes the table rows, so bad cells are fed inline; no fixture file and no network.
3. **`test_adapter_canvas_row` keywords unchanged here** — Story 2 moved the cursor keywords in the same commit as the row, so task 3.3 had nothing to update.
4. **Evaluator residuals** — the drift-log assertion was narrowed from "the file never mentions prototype.md" to "no DEV entry title names a Step 2.5 change", and the issue note's technical-spec path was made repo-root resolvable; the duplicated three-label assertion stays so AC-3.4 has its own citation.

### Test Results

**Verification:** Automated, test-first (`test_issue_verification_note` red before the issue note existed: 1 failed, 8 passed; the negative cases passed at once because `check_record` factors assertions Stories 1 and 2 already had).
**Coverage:** Not measured by the script (test and documentation changes only).

- ✅ Targeted: `scripts/tests/test_platform_neutral_names.py` → 48 passed.
- ✅ Full pytest (3.9): 2789 passed, 2 skipped.
- ✅ Bash tests: 45/45.
- ✅ `bash scripts/eval.sh`: Findings 0, run errors 0.
- ✅ Gate 3 review-override, Gate 3.5 drift-format, Gate 4 authenticity: pass; coverage, app-verify, docs-check: unverifiable (no coverage report, no recipe, no public exports). ac-trace: 0 findings.

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** None
- **Security:** Clean
- **Boundary Compliance:** both changed files are owned; `commands/prototype.md` and `drift-log.md` deliberately untouched.
- gate3-route: evaluator-agent. review-panel: off. arch-lint: none — see .writ/docs/architecture-lint.md.
- Gate 0 arch-check: pass (rederived proceed). Gate 2: no linter configured; build-smoke unverifiable (unsupported_stack). Gate 2.5: cross-component; boundary-map crossings 0.
- Residual left as taste: `test_check_record_rejects_bad_cells` repeats the no-data-row assertion in each parametrized case.

### Deviations from Spec

None.

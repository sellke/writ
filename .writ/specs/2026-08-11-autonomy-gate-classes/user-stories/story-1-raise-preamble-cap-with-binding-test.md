# Story 1: Raise the `_preamble` Cap and Prove It Still Binds

> **Status:** Complete
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer
**I want to** raise the `commands/_preamble.md` length limit from 80 to 95 against a stated budget, with a test proving the new limit still fails a file that exceeds it
**So that** the gate-class table can land without the cap quietly becoming decorative — the failure mode that already neutered the 2000-line command limit

## Acceptance Criteria

- [x] Given `scripts/eval.sh` `check_length()`, when the `_preamble` branch is inspected, then its test reads `-gt 95` and its finding message reads `limit 95` — both changed together, with the remediation hint unchanged.
- [x] Given a synthetic project root containing a 96-line `commands/_preamble.md`, when `bash scripts/eval.sh --check=length` runs, then it exits non-zero and the report contains `` `commands/_preamble.md`: 96 lines (limit 95). ``
- [x] Given the same harness with a 95-line `commands/_preamble.md`, when the check runs, then it exits 0 with no `_preamble` finding.
- [x] Given the same harness with a 2001-line `commands/example.md` and a 101-line `spec-lite.md`, when the check runs, then both still produce findings reading `limit 2000` and `limit 100` respectively — proving neither adjacent limit was touched.
- [x] Given the repository's real `commands/_preamble.md`, when it is grepped for `eval-exempt:`, then there is no match — the cap was resized, not bypassed.
- [x] Given the full diff of `scripts/eval.sh` produced by this story, when it is reviewed, then exactly two lines changed and both are inside the `_preamble` block.

## Implementation Tasks

- [x] 1.1 Re-verify the baseline before changing anything: `wc -l commands/_preamble.md` must still be 79. If it is not, re-derive the cap from the new baseline (`baseline + 14 + 2`) and record the recalculation in this story — do not stretch 95 to fit.
- [x] 1.2 Write the failing test first: a shell test in `scripts/tests/` (shape it after `scripts/tests/test_eval_leanness.sh`) that builds a temp project root — `scripts/eval.sh` copied in, a generated `commands/_preamble.md`, `mkdir -p .writ/state` — and runs `bash scripts/eval.sh --check=length` from it, asserting exit code **and** finding text.
- [x] 1.3 Add the four length assertions: 95 → exit 0; 96 → exit 1 with `limit 95`; a 2001-line command file → `limit 2000`; a 101-line `spec-lite.md` → `limit 100`. The last two are the ownership-boundary regressions.
- [x] 1.4 Add the exemption assertion: the real `commands/_preamble.md` contains no `eval-exempt:` marker.
- [x] 1.5 Change `scripts/eval.sh:411-412` — `-gt 80` → `-gt 95`, `limit 80` → `limit 95`. Leave the remediation hint, the `[ -f "$file" ]` guard, and the `file_has_exemption` guard alone.
- [x] 1.6 Run the new test — all assertions pass — then run `bash scripts/eval.sh --check=length` against the real repo and confirm exit 0 (the real preamble is still 79 lines at this point, well under either limit).
- [x] 1.7 Verify the diff scope: `git diff scripts/eval.sh` shows exactly two changed lines, both between the `file="$PROJECT_ROOT/commands/_preamble.md"` assignment and its closing `fi`.

## Notes

**Technical considerations:**

- `scripts/eval.sh` derives `PROJECT_ROOT` from `dirname "${BASH_SOURCE[0]}"/..` (line 13), which is what makes the fixture harness possible without any new flag or environment variable. Do not add a `--project-root` option to make testing easier — that is a change to a file this spec only partially owns, and the copy-into-temp-dir approach is already verified to work.
- Assert on finding **text**, not just exit code. `--check=length` runs three separate limits; a bare exit-code assertion cannot distinguish "the preamble cap fired" from "the spec-lite cap fired on a stray fixture".
- The check is `-gt`, so 95 lines is legal and 96 is not. Write both boundary cases; an off-by-one here silently shifts the budget.
- `line_count` is eval.sh's own helper. If it disagrees with `wc -l` on a file without a trailing newline, the boundary moves. Generate fixtures with trailing newlines and assert the exact counts rather than assuming agreement.
- The temp directory needs `.writ/state/` to exist — `eval.sh` writes its report there. Clean up on exit with a trap.

**Risks / challenges:**

- **The real risk in this story is not the edit; it is the justification.** A cap raised to accommodate content is not a cap. The budget (79 + 14 + 2 = 95) is fixed in the spec *before* Story 2 writes a word, and this story lands first specifically so the git history shows that ordering. If a reviewer cannot reconstruct where 95 came from without reading the finished preamble, this story failed.
- Adjacent-line collision: the `-gt 2000` command limit is eleven lines below the line being edited and is owned by the Phase 10 `governor-enforcement` work. An editor with a loose regex or a wide search-and-replace could take both. Tasks 1.3 and 1.7 exist to catch that.
- The tempting shortcut when a preamble grows again is `eval-exempt: length`, which removes the check rather than resizing it — silently, with no test failure anywhere. Task 1.4 is the tripwire.

**Integration points:**

- Story 2 cannot land its content until this story's cap is in place; authoring first would put the branch through a state where the CI Tier 1 gate fails.
- Phase 10's `governor-enforcement` spec edits `check_length` line 422 (2000 → 400). Both diffs are two lines wide and non-overlapping; a rebase resolves them, no semantic merge required.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## What Was Built

**Baseline re-verification (Task 1.1).** `wc -l commands/_preamble.md` = **79** at implementation start, matching the spec's stated baseline. No recalculation was required; the cap stays at the budgeted 79 + 14 + 2 = **95**.

**The change.** `scripts/eval.sh` lines 411-412 only — `-gt 80` → `-gt 95` and `limit 80` → `limit 95`. `git diff -U0 scripts/eval.sh` reports `@@ -411,2 +411,2 @@`: two lines changed, both inside the `_preamble` block. The remediation hint, the `[ -f "$file" ]` guard, and the `file_has_exemption` guard are untouched.

**The proof.** `scripts/tests/test_eval_length_caps.sh` — seven assertions, all green, and verified red before the change (95-line fixture failed with `limit 80`) and red again when the constant was temporarily reverted. It copies `scripts/eval.sh` into a temp project root and runs `--check=length` against synthetic content, asserting exit code **and** finding text:

| # | Scenario | Assertion |
|---|---|---|
| 1 | 95-line `_preamble.md` | exit 0, no `_preamble` finding |
| 2 | 96-line `_preamble.md` | exit 1, blocking `` `commands/_preamble.md`: 96 lines (limit 95). `` |
| 3 | 2001-line `commands/example.md` | still `limit 2000` — the adjacent limit this spec does not own |
| 4 | 101-line `spec-lite.md` | still `limit 100` — the other adjacent limit |
| 5 | 96-line `_preamble.md` + `eval-exempt: length` | exit 0, no finding — the bypass, demonstrated |
| 6 | real `commands/_preamble.md` | contains no `eval-exempt:` marker (Business Rule 4 tripwire) |
| 7 | real `commands/_preamble.md` | ≤ 95 lines |

Scenario 5 exists to make Scenario 6 legible: the exemption does not resize the cap, it deletes it, silently and with no other test noticing. Scenarios 3 and 4 are the ownership-boundary regressions — if either message ever changes, this spec edited a line it does not own.

**Harness notes.** `spec_lite_files()` enumerates through `git ls-files -co --exclude-standard`, so Scenario 4's fixture root is `git init`-ed; the file stays untracked, which `-o` covers, so no commit and no git identity are needed. `gen_lines` asserts that `awk 'END{print NR}'` (eval.sh's own `line_count`) and `wc -l` agree on every fixture, because a disagreement on a missing trailing newline would shift the 95/96 boundary by one and quietly void the whole test.

## Context for Agents

- **Business rules:** [Rule 1 (cap derived from a stated budget, not from measured content), Rule 2 (the cap must still bind, proven by test), Rule 3 (this spec owns exactly one constant in `check_length`), Rule 4 (no length exemption, ever)] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [The `_preamble.md` line budget; The `check_length` constant change; The regression test] — from spec.md → ## Detailed Requirements
- **Technical concerns:** [The cap change is the risk, not the table] — from spec.md → ## Technical Concerns
- **Contract:** [Hardest constraint: 79 lines against a hard 80-line cap producing a *blocking* finding; this spec owns only the `_preamble` length constant, not the command limit below it] — from spec.md → ## Contract (Locked)
- **Technical detail:** [Current `_preamble` block verbatim, the verified fixture-harness results, the exemption trap] — from sub-specs/technical-spec.md → ## Story 1

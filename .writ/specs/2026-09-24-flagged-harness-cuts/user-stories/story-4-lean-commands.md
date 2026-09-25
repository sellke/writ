# Story 4: Lean command bodies

> **Status:** Completed ✅ (2026-09-25)
> **Commit:** 3541b7eec4207218e72f7eb291d49d9ea867f0e8
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** Writ maintainer
**I want to** author lean sibling bodies for the four large commands behind `WRIT_HARNESS_LEAN`
**So that** flag-on runs load shorter command text without changing the default floor or dropping exit criteria, gates, or the production boundary

## Acceptance Criteria

> **AC IDs assigned through:** AC-4.4

- [x] Given `WRIT_HARNESS_LEAN` is unset, when `scripts/measure-invocation.py` reports the invocation floor, then `commands/create-spec.md`, `commands/verify-spec.md`, `commands/implement-phase.md`, and `commands/implement-story.md` are byte-identical to before this story and no `*.lean.md` sibling bytes are counted in that floor. `[AC-4.1]`
- [x] Given `WRIT_HARNESS_LEAN=1` and the four lean siblings exist, when `scripts/measure-invocation.py` reports the invocation floor, then it loads the lean bodies for create-spec, verify-spec, implement-phase, and implement-story. `[AC-4.2]`
- [x] Given the lean siblings `commands/create-spec.lean.md`, `commands/verify-spec.lean.md`, `commands/implement-phase.lean.md`, and `commands/implement-story.lean.md`, when each is inspected, then none contains a line that asks the model to conserve tokens, be brief, or avoid waste, and each retains exit criteria, named gates, and the production boundary (no autonomous merge, PR, or release). `[AC-4.3]`
- [x] Given lean bodies are authored, when the default command files are inspected, then neither text is embedded in the live `.md` command and the only lean command siblings this story creates are the four named files. `[AC-4.4]`

## Implementation Tasks

- [x] 4.1 Write tests that assert the unset floor excludes lean command siblings and stays byte-stable on the four defaults, that `WRIT_HARNESS_LEAN=1` reports the lean bodies, and that embedding both texts in a live command fails the floor check. `[AC-4.1, AC-4.2, AC-4.4]`
- [x] 4.2 Author `commands/create-spec.lean.md` (drop model-redundant and system-instructions restatement only; keep exit criteria, gates, production boundary). `[AC-4.3, AC-4.4]`
- [x] 4.3 Author `commands/verify-spec.lean.md` under the same deletion class. `[AC-4.3, AC-4.4]`
- [x] 4.4 Author `commands/implement-phase.lean.md` under the same deletion class. `[AC-4.3, AC-4.4]`
- [x] 4.5 Author `commands/implement-story.lean.md` under the same deletion class. `[AC-4.3, AC-4.4]`
- [x] 4.6 Verify acceptance criteria: unset floor excludes lean siblings and defaults are unchanged; flag-on reports lean bodies; no token-saving lines; gates and production boundary retained; run the new tests. `[AC-4.1, AC-4.2, AC-4.3, AC-4.4]`

## Notes

- Depends on Story 1's loader substrate in `scripts/measure-invocation.py`; this story authors bodies only and does not re-teach flag parsing.
- Contract constraint: four rewrites stay one story — one task per lean file plus a floor-measurement check — not four specs.
- Allowed cuts: behavior the current default frontier already does (Opus 5.5, or GPT-6 Astra — both above the Fable 5.1 baseline model), and sentences that restate `system-instructions.md`. Forbidden cuts: exit criteria, named gates, production boundary. Do not justify a cut by what only a weaker model needed.
- Story 5 (keep-or-revert) is the only story that may change the default load path.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [Load a lean sibling]
- **Shadow paths:** [Flag off assemble, Flag on assemble]
- **Business rules:** [No token-saving instruction, Deletion class, Siblings are not in the default floor]
- **Experience:** [Flag unset, Flag set, under budget]

---

## What Was Built

**Implementation Date:** 2026-09-25

### Files Created

1. **`commands/create-spec.lean.md`** (945 → 611 lines; 51,851 → 35,763 bytes)
   - Cut: Step 1.2 Plan Mode restatement, Step 2.1 `todo_write` tracking, discovery question banks (reduced to topics), rationale asides, Example Usage. `--recommend` section byte-identical to the default.
2. **`commands/verify-spec.lean.md`** (804 → 362 lines; 35,626 → 21,696 bytes)
   - Cut: JSON data-model example, pseudo-code blocks (now bullets), duplicate `--fix` regeneration steps, full report examples, Integration table. Checks 1–8 and P1–P4 with their dispositions kept.
3. **`commands/implement-phase.lean.md`** (369 → 338 lines; 35,160 → 27,343 bytes)
   - Cut: rationale asides, provenance notes, Integration table, example blocks reduced to placeholders. Added: "Validate the `--recommend` invocation matrix before any mutation."
4. **`commands/implement-story.lean.md`** (471 → 418 lines; 34,063 → 30,208 bytes)
   - Cut: rationale asides, repeated "this gate owns when / the skill owns how" sentences, duplicate `/prototype` note, example blocks. Step 2 runs `story-context.py` with the flag, reads `spill.path` when present, and spills What Was Built records over 1,000 lines.
5. **`scripts/tests/test_lean_commands.py`** (36 tests)
6. **`scripts/tests/test_eval_manifest_lean.sh`** (5 checks)

### Files Modified

- **`scripts/eval.sh`** (`check_manifest`)
  - Skips a `*.lean.md` only when `commands/<stem>.md` exists.
- **`scripts/eval-leanness.py`** (`is_lean_sibling`, `all_command_files`, `metrics["commands"]`)
  - Same sibling-only exclusion; surface byte and line totals still include lean files.

### Implementation Decisions

1. **Frontmatter verbatim except `name` and `description`** — `name: <stem>-lean`; description begins "Lean variant of /<stem> for WRIT_HARNESS_LEAN=1 baseline runs." `exit_criteria`, `loop`, and `gates` unchanged (test-asserted).
2. **Every gate, verdict script, AskQuestion, loop bound, and Terminal constraint kept** — the kept-heading and kept-script lists are checked against the defaults so they cannot pass vacuously.
3. **Production boundary line in each Completion section** — names the command's actual writes and forbids merge, PR, release, tag, and publish.
4. **Lean preamble by link** — references name `commands/_preamble.lean.md` and its sibling `commands/_preamble.md` (keeps eval's preamble-reference check passing).
5. **Four default commands byte-identical** — sha256 pinned in tests.

### Test Results

**Verification:** Automated
- ✅ Red first: 17 failures before the lean files existed; each eval-exclusion and orphan test red before its fix
- ✅ `uv run --python 3.9 pytest -q` — 1330 passed, 1 skipped
- ✅ All `scripts/tests/test_*.sh` pass
- ✅ `bash scripts/eval.sh` — exit 0, Findings: 0 (non-blocking warnings: `commands.lines` / `commands.chars` growth from the lean files, ~115KB)
- ✅ Flag-off floor hash `84f2c4c2…c359` unchanged
- ✅ `test-integrity.py coverage` — pass; `scripts/eval-leanness.py` 92%
- ⚠️ `test-integrity.py authenticity` — `test_imports_no_source`, known checker false positive (see Story 1). Not DEGRADED.
- ⚠️ Gate 3 `review-override.py` — `fail` `dangling_reference` for `AC-4.5`, cited only by `scripts/tests/test_boundary_map.py` (another spec). Cross-spec collision; evaluator PASS stands.
- Mechanical: drift-format `pass`; docs-check `unverifiable` (`no_public_exports`)

**Coverage:** 92% line coverage on `scripts/eval-leanness.py`

### Review Outcome

**Result:** PASS

- **Iteration count:** 2 iteration(s) — cycle 1 FAIL (Major: the implement-story lean boundary line said the story commit was the only git write, contradicting Step 4 item 7; Minor: create-spec boundary wording, orphan lean files hidden by eval), fixed in recode
- **Drift:** Small
- **Security:** Clean
- **Boundary Compliance:** Four lean files plus tests; two eval scripts touched outside the task list (DEV-009).

### Deviations from Spec

- **[DEV-008] What Was Built spill lives in the lean command, not a lean skill branch** — Severity: Small — Auto-amended
- **[DEV-009] eval.sh and eval-leanness.py edited outside the story's listed files** — Severity: Small — Auto-amended

### Open items for Story 5

- Lean siblings ship to user projects: `install.sh` / `update.sh` copy every `commands/*.md`, so the four lean commands would be invocable there. Decide: exclude `*.lean.md` from install/update, or ship deliberately.
- `eval.sh` pins "Narrow Recommended-Delivery Exception" on `_preamble.md`; a keep that flips the default needs a new target.
- The lean bodies add ~115KB to the commands surface (non-blocking leanness warnings).

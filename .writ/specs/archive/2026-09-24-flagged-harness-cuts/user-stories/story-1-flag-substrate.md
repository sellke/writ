# Story 1: Flag substrate

> **Status:** Completed ✅ (2026-09-25)
> **Commit:** d647b18b795fee18185f0b09af7adffa430b18ee
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer
**I want to** teach `measure()` in `scripts/measure-invocation.py` to honor `WRIT_HARNESS_LEAN` so unset keeps today’s floor and `1` selects `commands/*.lean.md` siblings without embedding them in the live command
**So that** the three harness cuts can ship default-off with a byte-identical flag-off path and a gated lean load path

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.4

- [x] Given `WRIT_HARNESS_LEAN` is unset and at least one `commands/*.lean.md` sibling exists on disk, when `measure()` builds the invocation floor, then the floor bytes are identical to today’s loader and contain none of the lean sibling bytes `[AC-1.1]`
- [x] Given `WRIT_HARNESS_LEAN=1` and a lean sibling exists for a measured command (or preamble), when `measure()` builds the invocation floor, then it loads that `*.lean.md` sibling instead of the default file `[AC-1.2]`
- [x] Given `WRIT_HARNESS_LEAN` is set to any value other than `1` (for example `yes`), when `measure()` runs, then it treats the flag as unset, emits exactly one warning that names the value, and loads the default files `[AC-1.3]`
- [x] Given `WRIT_HARNESS_LEAN=1` and a required lean sibling is missing, when `measure()` builds the invocation floor, then it loads the default file and emits a warning that names the missing sibling path `[AC-1.4]`

## Implementation Tasks

- [x] 1.1 Write tests in `scripts/tests/` (pytest, Python 3.9) for `measure()` flag substrate: unset floor excludes lean bytes; `=1` selects an existing sibling; other values warn once and use default; missing sibling warns with path and loads default — clear the env var in default-path cases `[AC-1.1, AC-1.2, AC-1.3, AC-1.4]`
- [x] 1.2 Add `WRIT_HARNESS_LEAN` readout inside `measure()` (and any helper it needs) so only the literal value `1` enables lean selection; any other set value is treated as unset with one warning naming the value `[AC-1.3]`
- [x] 1.3 When the flag is `1`, resolve preamble and command paths to `*.lean.md` siblings when present; keep lean files out of `_L.all_command_files` / the default floor enumeration so unset measurement never counts them `[AC-1.1, AC-1.2]`
- [x] 1.4 When the flag is `1` and a sibling is absent, fall back to the default file and append a warning that names the missing path `[AC-1.4]`
- [x] 1.5 Verify acceptance criteria: unset floor hash/byte count matches pre-change behavior with lean fixtures present; flag-on loads siblings; invalid values and missing siblings match the Error & Rescue Map rows `[AC-1.1, AC-1.2, AC-1.3, AC-1.4]`
- [x] 1.6 Verify all tests pass: `uv run --python 3.9 pytest scripts/tests/` for the new flag-substrate module (and any existing `measure-invocation` tests still green) `[AC-1.1, AC-1.2, AC-1.3, AC-1.4]`

## Notes

**Technical considerations.** The floor builder is `measure()` in `scripts/measure-invocation.py` (`floor_bytes = base_bytes + command_bytes + eager_bytes`). Lean selection must change which path feeds `_read_bytes` / counted labels for preamble and command bodies — not inject a second copy into the live command. Tests live under `scripts/tests/`; do not modify product commands in this story.

**Risks.** Accidental `WRIT_HARNESS_LEAN` in the test process would poison default-path assertions — clear it first. Enumerating `*.lean.md` as ordinary commands would inflate the unset floor and fail the byte-identical gate.

**Integration.** No story dependencies. Stories 2–4 author lean siblings and spill; Story 5 may flip the default. This story only gates the loader.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [Read the flag, Load a lean sibling]
- **Shadow paths:** [Flag off assemble, Flag on assemble]
- **Business rules:** [Siblings are not in the default floor, No token-saving instruction]
- **Experience:** [Entry point (`WRIT_HARNESS_LEAN`), State catalog — Flag unset]

---

## What Was Built

**Implementation Date:** 2026-09-25

### Files Created

1. **`scripts/tests/test_measure_invocation_lean.py`** (16 tests)
   - Flag-substrate tests: FlagUnset (4), FlagOn (5), FlagInvalid (3), MissingSibling (4). Every test pins `WRIT_HARNESS_LEAN` and removes `ANTHROPIC_API_KEY`.

### Files Modified

- **`scripts/measure-invocation.py`** (`measure()`, new `_harness_lean`, `_resolve_lean`, constants)
  - `LEAN_ENV`, `LEAN_SUFFIX`, `LEAN_SIBLINGS` constants; flag readout; one resolver for the preamble and command paths; `*.lean.md` filtered from command enumeration; `harness_lean` and per-command `source` fields only when the flag is on; one Usage line.

### Implementation Decisions

1. **Only the literal `1` enables the flag** — any other set value, the empty string included, warns once with `repr(value)` and loads the defaults.
2. **Lean files are never measured as commands**, flag on or off — `eval-leanness.py`'s glob would otherwise count `foo.lean.md` as a command named `foo.lean`.
3. **Resolved path replaces the default** — bytes, lines, tokens, frontmatter, and inline reads all come from the one file actually loaded, so no second copy enters the floor.
4. **New report fields only under the flag** — keeps the flag-off JSON byte-identical.

### Test Results

**Verification:** Automated
- ✅ Red first: 14 of 16 new tests failed before implementation (the two that passed were flag-off cases that already held)
- ✅ `uv run --python 3.9 pytest -q` — 1263 passed, 1 skipped, 0 failed
- ✅ Flag-off floor hash `84f2c4c2…c359` matches pre-change, on the repo and on a scratch copy with lean siblings added
- ✅ `test-integrity.py coverage` — pass; `scripts/measure-invocation.py` 96% (HEAD 95%)
- ⚠️ `test-integrity.py authenticity` — `test_imports_no_source` (blocking). Known checker false positive: tests load hyphenated scripts via `spec_from_file_location`; `test_measure_invocation.py` fails identically at HEAD (issue `2026-09-03-test-integrity-authenticity-flags-every-bash-test.md`). Red-then-green is the binding proof. Not DEGRADED.
- ⚠️ Gate 3 `review-override.py` — `fail` `dangling_reference` for `AC-1.5`…`AC-5.5`, cited only by other specs' tests (`test_eval_pruned_base.sh`, `test_arch_check.py`, `test_docs_check.py`, `test_boundary_map.py`, `test_eval_entry_level_note.sh`). Cross-spec AC-ID collision, same as Stage 3 Story 3. Recoding this story cannot clear it. Evaluator PASS stands.
- Mechanical: arch-check `pass` (rederived proceed); drift-format `pass`; docs-check `unverifiable` (`no_public_exports`); build-smoke `unverifiable` (`unsupported_stack`)

**Coverage:** 96% line coverage on `scripts/measure-invocation.py`

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** Small
- **Security:** Clean
- **Boundary Compliance:** Boundary map owned `scripts/tests/` only; `scripts/measure-invocation.py` is named by the story's tasks. No `commands/` edits.

### Deviations from Spec

- **[DEV-001] Existing loader warnings name the file actually loaded** — Severity: Small
  - Resolution: Auto-amended (spec-lite Implementation Approach)
- **[DEV-002] Missing-sibling warnings limited to the five in-scope siblings** — Severity: Small
  - Resolution: Auto-amended (spec-lite Implementation Approach)

### Forward risk for Stories 2–4

`eval-leanness.py` `all_command_files` still globs `commands/*.md`; its callers (including `command_names` and the README check) will see `*.lean.md` as commands once siblings exist.

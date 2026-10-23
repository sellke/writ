# Story 2: Ship, Link, and Pin the Guide

> **Status:** Completed ✅
> **Commit:** 9c21831ce494afd722b12ddea79cc55e709a30e6
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** new user reading the README before my first request, and the maintainer who must keep the guide shipped **I want to** see a pointer to the guide in README Quick Start, backed by tests that fail if the link or the ship-set entry is lost **So that** I read the guide before my first command, and installed projects keep receiving it.

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.5

- [x] Given `README.md` § Quick Start, when its text is read in order, then the paragraph `New here? Read [`.writ/docs/prompting-guide.md`](.writ/docs/prompting-guide.md) (two minutes).` appears before the five-command table, and it has no `/writ` clause `[AC-2.1]`
- [x] Given `scripts/tests/test_prompting_guide.py`, when `test_readme_links_guide` reads `README.md` from the `## Quick Start` heading to the next H2, then the test passes when that text contains `.writ/docs/prompting-guide.md` and fails when it does not `[AC-2.2]`
- [x] Given `scripts/install.sh` and `scripts/update.sh`, when `test_ships` extracts `is_shippable_writ_doc` with `sed -n '/^is_shippable_writ_doc()/,/^}/p'`, sources it in a `bash` subprocess, and calls it with `prompting-guide.md`, then the call exits 0 in both scripts `[AC-2.3]`
- [x] Given `scripts/tests/test_prompting_guide.py` with the two new tests added, when `uv run --python 3.9 pytest scripts/tests/test_prompting_guide.py` runs, then all seven tests pass, and no second test file for the guide exists `[AC-2.4]`
- [x] Given the guide and the README change, when `bash scripts/eval.sh` runs outside any sandbox, then it reports 0 findings, including none from `check_broken_refs` or a length cap on the guide `[AC-2.5]`

## Implementation Tasks

- [x] 2.1 Add `test_readme_links_guide` and `test_ships` to the existing `scripts/tests/test_prompting_guide.py`, in the style of `scripts/tests/test_platform_neutral_names.py`. `test_readme_links_guide` reads the `## Quick Start` section of `README.md`. `test_ships` runs the `sed` extraction for each script in a `bash -c` subprocess and passes `prompting-guide.md` as an argument. Run the file: `test_readme_links_guide` must fail, and `test_ships` passes on arrival, which is expected (see Notes) `[AC-2.2, AC-2.3]`
- [x] 2.2 Insert the AC-2.1 paragraph in `README.md` § Quick Start, directly under the `## Quick Start` heading and above the "Writ ships 32 commands" sentence, so that sentence's colon still leads into the table. Use the exact text with no `/writ` clause. Rerun the file: `test_readme_links_guide` passes `[AC-2.1, AC-2.2]`
- [x] 2.3 Confirm `scripts/install.sh` and `scripts/update.sh` carry the same ship-set function: `diff` the `sed` extraction from each script, then call the function with `prompting-guide.md` and confirm exit 0 `[AC-2.3]`
- [x] 2.4 Run `uv run --python 3.9 pytest scripts/tests/test_prompting_guide.py`. Confirm all seven tests pass, and `ls scripts/tests | grep -i prompting` lists one file `[AC-2.4]`
- [x] 2.5 Run `uv run --python 3.9 pytest` and `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`. Confirm no failures caused by this story `[AC-2.4]`
- [x] 2.6 Run `bash scripts/eval.sh` outside any sandbox. Confirm 0 findings, with no `check_broken_refs` or length-cap finding for the guide or the README `[AC-2.5]`

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Notes

- **Dependency:** Story 1 creates `.writ/docs/prompting-guide.md` and the five tests in `scripts/tests/test_prompting_guide.py`. Keep those test names and helpers unchanged. `check_referenced_paths` in `scripts/eval.sh` needs the guide file to exist before `2026-10-22-front-door` cites it, so Story 1 lands first.
- **Pointer placement:** Directly under the `## Quick Start` heading. A paragraph between the "Writ ships 32 commands" sentence and the table would break that sentence's lead-in colon.
- **`/writ` clause:** The front-door spec adds it (technical-spec.md → ## README Change). `test_readme_links_guide` checks only the path, so that later edit does not break the test. Do not pin the full sentence in the test.
- **`test_ships` passes on arrival:** The denylist already admits the file (technical-spec.md → ## Current State). The test pins that admission. It turns red only if `is_shippable_writ_doc` is renamed or restructured. Fix the test's extraction, not the guide (technical-spec.md → ## Shadow Paths).
- **Subprocess form:** Pass the script path and the filename as arguments to `bash -c`, not interpolated into the command string. Python 3.9 stdlib only.
- **Future allowlist:** Business Rule 5 requires the guide on any allowlist (spec.md → ## Business Rules (Expanded)). The exclusions proposed in `2026-10-21-dev-only-docs-ship-to-users` (`leanness-audit-2*.md`, `swot-*.md`) do not match the guide's name (spec.md → ## Technical Concerns).
- **Eval:** `bash scripts/eval.sh` runs `git init` in a temp dir, so run it outside any sandbox.

## Context for Agents

- **Error map rows:** []
- **Shadow paths:** `technical-spec.md → ## Shadow Paths` (Happy path, Upstream error)
- **Business rules:** `spec.md → ## Business Rules (Expanded)` (5. Ships)
- **Experience:** `spec.md → ## Experience Design → ### State Catalog` (Fresh install, README Quick Start)

---

## What Was Built

**Implementation Date:** 2026-10-22

### Files Created

[None created]

### Files Modified

- **`README.md`** (§ Quick Start, lines 215 to 216)
  - Inserted the paragraph `New here? Read [`.writ/docs/prompting-guide.md`](.writ/docs/prompting-guide.md) (two minutes).` plus one blank line directly under `## Quick Start`, above the unchanged "Writ ships 32 commands" sentence, so its colon still leads into the table. No `/writ` clause (the front-door spec adds it).
- **`scripts/tests/test_prompting_guide.py`** (docstring Story 2 section; `import subprocess`; constants `README`, `QUICK_START`, `SHIP_FUNCTION`, `SHIP_SCRIPTS`, `GUIDE_NAME`, `NO_FUNCTION`, `SHIP_SNIPPET`; `test_readme_links_guide`; `test_ships`)
  - `test_readme_links_guide` slices `README.md` from `## Quick Start` to the next H2 with the existing `section()` helper and asserts the slice names `.writ/docs/prompting-guide.md` (path only; the sentence is read by hand because the front-door spec appends to it). `test_ships` runs, for each of `scripts/install.sh` and `scripts/update.sh`, `["bash", "-c", SHIP_SNIPPET, "bash", <script>, "prompting-guide.md"]` with `cwd=REPO_ROOT`: the snippet extracts the function with `sed -n '/^is_shippable_writ_doc()/,/^}/p' "$1"`, exits 64 when the extraction is empty (the test then fails naming the script and the function), sources it from a here-string, and calls it with `"$2"`; exit 0 is asserted. The five Story 1 tests and helpers are unchanged (76 insertions, 0 deletions).
- **`.writ/specs/2026-10-22-prompting-guide/drift-log.md`** — Story 2 section with DEV-004.

### Implementation Decisions

1. **Here-string sourcing, not process substitution** — on macOS `/bin/bash` 3.2.57 the spec's sketched `source <(sed …)` defines nothing and exits 127 (verified by the orchestrator and the evaluator); `source /dev/stdin <<<"$fn"` exits 0 on bash 3.2.57 and 5.3.20. Same `sed` expression, same `bash` subprocess, same call (DEV-004).
2. **Script path and filename as positional arguments** — passed after `"bash"` in the argv list, never interpolated into the snippet (story Notes).
3. **Extraction failure is a distinct exit code (64)** — realizes the technical spec's "Upstream error" shadow path: a renamed or restructured `is_shippable_writ_doc` fails on extraction with "fix this test's extraction, not the guide", separate from the function's own 0/1.
4. **Loop, not `parametrize`** — keeps the file at seven collected tests, which AC-2.4 counts.
5. **Docstring tokens** — `AC-2.2` and `AC-2.3` are asserted; `AC-2.1` (exact sentence and placement), `AC-2.4` (the run of this file), and `AC-2.5` (`bash scripts/eval.sh`) are declared as read-by-hand or verification runs in the sentence that carries each token, the Story 1 precedent.

### Test Results

**Verification:** Automated, test-first (`test_readme_links_guide` red on the unlinked README, green after the insert; `test_ships` green on arrival as the story Notes predict, with its missing-function branch exercised by hand against `README.md` → exit 64 and its rejection branch against `recommended-delivery-state-format.md` → exit 1).
**Coverage:** Not measured by the script (no coverage report; documentation and test changes only).

- ✅ Targeted: `uv run --python 3.9 pytest scripts/tests/test_prompting_guide.py` → 7 passed; `ls scripts/tests | grep -i prompting` → one file.
- ✅ Full pytest (3.9): 2796 passed, 2 skipped.
- ✅ Bash tests: 45 run, 0 failed.
- ✅ `bash scripts/eval.sh`: Findings 0, Run errors 0 (`.writ/state/eval-20261023-004638.md`).
- ✅ Task 2.3: the `sed` extractions from `scripts/install.sh` and `scripts/update.sh` are byte-identical; `is_shippable_writ_doc prompting-guide.md` exits 0 in both.
- ✅ Gate 0 arch-check: pass (rederived proceed). Gate 2: no linter configured; arch-lint: none — see .writ/docs/architecture-lint.md; build-smoke unverifiable (unsupported_stack). Gate 2.5: cross-component, 0 crossings. Gate 3 review-override: unverifiable (no_coverage_report); ac-trace: 0 findings on the Completed story. Gate 3.5 drift-format: pass. Gate 4 coverage: unverifiable (no_coverage_report); authenticity: pass (Story 1's `test_imports_no_source` cleared by `test_ships`'s project-script reference). Gate 4.5 app-verify: unverifiable (no_recipe). Gate 5 docs-check: unverifiable (no_public_exports).

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** Small (DEV-004)
- **Security:** None (argv list, `cwd=REPO_ROOT`, no `shell=True`; only the repo's own scripts are sourced)
- **Boundary Compliance:** only the owned paths changed (`README.md`, `scripts/tests/test_prompting_guide.py`); `scripts/install.sh` and `scripts/update.sh` read, not modified; no deviation, no violation.
- gate3-route: evaluator-agent. review-panel: unverifiable (platform_cannot_spawn_other_vendors). jev-shadow: unverifiable (no_api_key). arch-lint: none — see .writ/docs/architecture-lint.md.
- Evaluator residuals, not drift: `NO_FUNCTION = 64` and the snippet's `exit 64` are duplicated by hand; the `AC-2.4`/`AC-2.5` docstring tokens satisfy ac-trace by presence (declared as runs, not assertions). The README has no Markdown H1 (the banner is HTML), so `section()`'s stop rule equals "to the next H2".
- Coding agent and evaluator ran as nested `general-purpose` spawns with the prompt templates from `agents/coding-agent.md` and `agents/evaluator-agent.md`.

### Deviations from Spec

- **[DEV-004] Ship-set function sourced from a here-string instead of process substitution** — Severity: Small
  - Spec said: Implementation Approach sketch `bash -c 'source <(sed -n "/^is_shippable_writ_doc()/,/^}/p" scripts/install.sh); is_shippable_writ_doc prompting-guide.md'`, exit 0.
  - Reality: same `sed`, subprocess, and call; the extraction is captured and sourced from a here-string, because the sketched form exits 127 on bash 3.2.57.
  - Resolution: Auto-amended; no spec-lite change needed (spec-lite names no sourcing form).

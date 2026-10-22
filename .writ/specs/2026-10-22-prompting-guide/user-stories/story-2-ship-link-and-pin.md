# Story 2: Ship, Link, and Pin the Guide

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** new user reading the README before my first request, and the maintainer who must keep the guide shipped **I want to** see a pointer to the guide in README Quick Start, backed by tests that fail if the link or the ship-set entry is lost **So that** I read the guide before my first command, and installed projects keep receiving it.

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.5

- [ ] Given `README.md` § Quick Start, when its text is read in order, then the paragraph `New here? Read [`.writ/docs/prompting-guide.md`](.writ/docs/prompting-guide.md) (two minutes).` appears before the five-command table, and it has no `/writ` clause `[AC-2.1]`
- [ ] Given `scripts/tests/test_prompting_guide.py`, when `test_readme_links_guide` reads `README.md` from the `## Quick Start` heading to the next H2, then the test passes when that text contains `.writ/docs/prompting-guide.md` and fails when it does not `[AC-2.2]`
- [ ] Given `scripts/install.sh` and `scripts/update.sh`, when `test_ships` extracts `is_shippable_writ_doc` with `sed -n '/^is_shippable_writ_doc()/,/^}/p'`, sources it in a `bash` subprocess, and calls it with `prompting-guide.md`, then the call exits 0 in both scripts `[AC-2.3]`
- [ ] Given `scripts/tests/test_prompting_guide.py` with the two new tests added, when `uv run --python 3.9 pytest scripts/tests/test_prompting_guide.py` runs, then all seven tests pass, and no second test file for the guide exists `[AC-2.4]`
- [ ] Given the guide and the README change, when `bash scripts/eval.sh` runs outside any sandbox, then it reports 0 findings, including none from `check_broken_refs` or a length cap on the guide `[AC-2.5]`

## Implementation Tasks

- [ ] 2.1 Add `test_readme_links_guide` and `test_ships` to the existing `scripts/tests/test_prompting_guide.py`, in the style of `scripts/tests/test_platform_neutral_names.py`. `test_readme_links_guide` reads the `## Quick Start` section of `README.md`. `test_ships` runs the `sed` extraction for each script in a `bash -c` subprocess and passes `prompting-guide.md` as an argument. Run the file: `test_readme_links_guide` must fail, and `test_ships` passes on arrival, which is expected (see Notes) `[AC-2.2, AC-2.3]`
- [ ] 2.2 Insert the AC-2.1 paragraph in `README.md` § Quick Start, directly under the `## Quick Start` heading and above the "Writ ships 32 commands" sentence, so that sentence's colon still leads into the table. Use the exact text with no `/writ` clause. Rerun the file: `test_readme_links_guide` passes `[AC-2.1, AC-2.2]`
- [ ] 2.3 Confirm `scripts/install.sh` and `scripts/update.sh` carry the same ship-set function: `diff` the `sed` extraction from each script, then call the function with `prompting-guide.md` and confirm exit 0 `[AC-2.3]`
- [ ] 2.4 Run `uv run --python 3.9 pytest scripts/tests/test_prompting_guide.py`. Confirm all seven tests pass, and `ls scripts/tests | grep -i prompting` lists one file `[AC-2.4]`
- [ ] 2.5 Run `uv run --python 3.9 pytest` and `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`. Confirm no failures caused by this story `[AC-2.4]`
- [ ] 2.6 Run `bash scripts/eval.sh` outside any sandbox. Confirm 0 findings, with no `check_broken_refs` or length-cap finding for the guide or the README `[AC-2.5]`

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

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

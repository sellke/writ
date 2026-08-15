# Story 1: install.sh — marker-based CLAUDE.md merge on initial install

> **Status:** Completed ✅ (2026-08-13)
> **Priority:** High
> **Dependencies:** None
> **Commit:** 16048cd6ceeb8cb38b9b977cc7cab45cde7bffea

## User Story

**As a** developer installing Writ into a project via `bash install.sh --platform claude` (fresh install or first-time Claude-platform install), who may already have a hand-written `CLAUDE.md` in their repo root predating Writ
**I want to** have `install.sh` merge Writ's `CLAUDE.md` content into a marker-bounded block instead of unconditionally overwriting the whole file
**So that** my pre-existing hand-written `CLAUDE.md` content is never silently destroyed, matching the safety `AGENTS.md` already has on the Codex platform

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.5

- [x] Given no `CLAUDE.md` exists in the target project, when `install.sh --platform claude` runs its apply path, then `merge_claude_md` creates `CLAUDE.md` wrapped in `<!-- writ:start -->`/`<!-- writ:end -->` markers with Writ's upstream content inside, and the apply path (install.sh:1053-1057) calls `merge_claude_md` instead of `cp "$WRIT_SRC/claude-code/CLAUDE.md" "CLAUDE.md"` `[AC-1.1]`
- [x] Given a `CLAUDE.md` exists with hand-written content and no `writ:start`/`writ:end` markers, when `install.sh --platform claude` runs, then the wrapped Writ block is appended below the existing content (handling a missing trailing newline first), and every byte of the original content above the block is preserved unchanged `[AC-1.2]`
- [x] Given a `CLAUDE.md` exists with malformed markers (marker count != 1 start or != 1 end, or start_line >= end_line), when `install.sh --platform claude` runs, then `merge_claude_md` returns non-zero (13, matching `merge_agents_md`'s convention), prints an error, and does not write to the file at all `[AC-1.3]`
- [x] Given a `CLAUDE.md` exists with well-formed markers whose inner-block hash matches neither the upstream template hash nor the manifest's `CLAUDE.md.writ-block` baseline hash, when `install.sh --platform claude` runs without `--force`, then the file is left untouched and a warning is printed; when the same run is repeated with `--force`, then the inner block is overwritten with upstream content while everything outside the markers remains untouched `[AC-1.4]`
- [x] Given `install.sh --platform claude` completes an apply run, when `write_copy_manifest` runs, then it writes `CLAUDE.md.writ-block` (computed via `writ_compute_writ_block_inner_hash "CLAUDE.md"`) instead of the old bare `CLAUDE.md` whole-file hash key; and given `install.sh --platform claude --dry-run` runs instead, then the preview output (replacing the hardcoded `Root: CLAUDE.md → always updated` line at install.sh:951-952) reports the real decision-tree outcome (new/append/update/preserved) via a `merge_claude_md preview` call `[AC-1.5]`

## Implementation Tasks

- [x] 1.1 Write `scripts/tests/test_merge_claude_md.sh` mirroring `scripts/tests/test_merge_agents_md.sh`'s structure (`setup_ws`, bundle extraction via `awk` between the `# <<< writ-merge-bundled-begin/end >>>` markers, `run()` helper, one `mktemp -d` workspace per scenario), covering: file absent, no markers, clean markers matching upstream (no-op), malformed markers, locally-modified block without `--force`, and locally-modified block with `--force` `[AC-1.1, AC-1.2, AC-1.3, AC-1.4]`
- [x] 1.2 Implement `merge_claude_md` inside/adjacent to the bundle block at install.sh:141-397, structurally parallel to `merge_agents_md` (install.sh:235-396), operating on `CLAUDE.md` / `claude-code/CLAUDE.md`, supporting `preview` and `apply` modes, and reusing `writ_block_marker_counts`, `writ_compute_writ_block_inner_hash`, `writ_file_ends_with_newline`, and `writ_rewrite_agents_md_with_inner` (or file-agnostic equivalents) rather than duplicating their logic `[AC-1.1, AC-1.2, AC-1.3]`
- [x] 1.3 Implement the malformed-marker and `--force` branches of `merge_claude_md`'s decision tree: return 13 with no write on malformed markers; on well-formed markers, compare inner hash against upstream and manifest baseline (`CLAUDE.md.writ-block`) to pick no-op/update/preserved-with-warning, and let `--force` collapse all three to an overwrite `[AC-1.3, AC-1.4]`
- [x] 1.4 Replace the unconditional `cp "$WRIT_SRC/claude-code/CLAUDE.md" "CLAUDE.md"` at install.sh:1053-1057 with a call to `merge_claude_md` in apply mode `[AC-1.1]`
- [x] 1.5 Replace the hardcoded `echo "  Root:    CLAUDE.md → always updated"` line at install.sh:951-952 with a `merge_claude_md preview` call (same pattern as the codex branch's `merge_agents_md preview` at install.sh:955), and update the claude branch of `write_copy_manifest` (install.sh:520-530) to write `CLAUDE.md.writ-block` via `writ_compute_writ_block_inner_hash "CLAUDE.md"` instead of the bare `CLAUDE.md` whole-file hash key `[AC-1.5]`
- [x] 1.6 Verify each acceptance criterion end-to-end: run `install.sh --platform claude` against fresh, no-marker, malformed-marker, and locally-modified fixture directories (with and without `--force`), and inspect both the resulting `CLAUDE.md` and the manifest's `CLAUDE.md.writ-block` entry `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`
- [x] 1.7 Run `bash scripts/tests/test_merge_claude_md.sh` and the existing `scripts/tests/test_merge_agents_md.sh` (to confirm no regression to the shared bundle helpers) and confirm all tests pass `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`

## Notes

- `merge_claude_md` must live inside (or directly adjacent to, within) the same `# <<< writ-merge-bundled-begin ... >>>` / `# <<< writ-merge-bundled-end >>>` block as `merge_agents_md` (install.sh:141/397) — the new test file extracts this chunk via `awk` the same way `test_merge_agents_md.sh` does, so misplacing the function breaks test bundle-extraction, not just the runtime behavior.
- This story only touches `install.sh`. `update.sh`'s equivalent `merge_claude_md` (including its `restore`/pre-fix-manifest-upgrade handling) is a separate, structurally-duplicated implementation per the spec's "no shared sourcing between standalone curl-pipeable scripts" constraint — out of scope here, tracked elsewhere in this spec.
- The manifest schema change (`CLAUDE.md.writ-block` replacing the bare `CLAUDE.md` key) is a one-way migration for this story's scope: a manifest with only the old bare key has no `CLAUDE.md.writ-block` baseline, so a pre-fix install's `CLAUDE.md` (unmarked) correctly falls into the "no markers found → append" path on first encounter, not "malformed" or "preserved" — this is called out explicitly because it's easy to mis-implement as an error case.
- Reuse existing helpers exactly as named in the contract (`writ_block_marker_counts`, `writ_compute_writ_block_inner_hash`, `writ_file_ends_with_newline`, `writ_rewrite_agents_md_with_inner`) — they already take a `$file` parameter and are file-agnostic; do not fork parallel `_claude_` variants of these helpers.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Business rules:** Decision tree (spec.md → 📋 Business Rules (detailed) → "Decision tree (both scripts, per merge_agents_md precedent)", steps 1-7); manifest migration semantics for pre-fix installs (spec.md → 📋 Business Rules (detailed) → "Manifest migration"); one shared manifest key `CLAUDE.md.writ-block` fully replacing the bare `CLAUDE.md` key (spec.md → Specification Contract → 📋 Business Rules, first bullet); content outside markers is never touched under any code path including `--force` (spec.md → Specification Contract → 📋 Business Rules, third bullet).
- **Shadow paths:** Pre-existing hand-written `CLAUDE.md` with no markers (spec.md → 🎯 Experience Design → "Happy path (pre-existing hand-written file)"); malformed-marker error path (spec.md → 🎯 Experience Design → "Error experience").
- **Experience:** Per-file console feedback lines for new/appended/preserved outcomes, and truthful `--dry-run` preview output replacing today's hardcoded claim (spec.md → 🎯 Experience Design → "Feedback model" and "Happy path" bullets).
- **Technical concerns:** `merge_claude_md` is a same-file structural duplicate of `merge_agents_md`, not a shared library extraction — comment it "keep synced" per existing convention, since `update.sh`'s independent copy is out of this story's scope (spec.md → ⚠️ Technical Concerns, first bullet).

---

## What Was Built

**Implementation Date:** 2026-08-13

### Files Created

1. **`scripts/tests/test_merge_claude_md.sh`** (9 scenarios)
   - Mirrors `scripts/tests/test_merge_agents_md.sh`'s structure. Covers: file absent (create), no-markers-append (non-empty and empty-file variants), clean-markers-update-from-baseline, clean-markers-no-op-matching-upstream, malformed-markers-error, preserved-without-force, force-overwrite, and missing-upstream-template (return 12). The last three (empty-file, missing-upstream-template) were added at Gate 4 to close two spec-lite shadow-path gaps the original 7 didn't cover.

### Files Modified

- **`scripts/install.sh`** (+~185/-7 lines)
  - New `merge_claude_md()` function (~lines 398-563), inside the same `# <<< writ-merge-bundled-begin/end >>>` block as `merge_agents_md`, implementing the full 7-branch decision tree (create/append/malformed-error/no-op/update-from-baseline/preserve-with-warning/force-collapse) and setting a distinct `CLAUDE_MERGE_NOTE` global on every path.
  - `write_copy_manifest`'s claude branch (~lines 700-708): now writes the `CLAUDE.md.writ-block` inner hash (guarded, mirroring the existing `AGENTS.md.writ-block` write), replacing the old bare whole-file `CLAUDE.md` hash key.
  - Dry-run preview (~lines 1120-1121): replaced the hardcoded "Root: CLAUDE.md → always updated" line with a real `merge_claude_md preview` call.
  - Apply path (~lines 1222-1224): replaced the unconditional `cp` with a bare `merge_claude_md apply` call (error propagation via `set -euo pipefail` preserved — not wrapped in `if`).
  - Post-apply summary block (~lines 1280-1284): added a claude-platform branch echoing `CLAUDE_MERGE_NOTE`, parallel to the existing codex branch (closes a Gate 0 CAUTION finding — this wasn't in the original task list).
- **`README.md`** (1 line): updated the Claude Code one-line-install description to describe the new merge/preserve behavior instead of the old implicit-overwrite phrasing, for parity with the adjacent Codex section's existing accurate description.

### Implementation Decisions

1. Reused all four existing bundle helpers (`writ_block_marker_counts`, `writ_compute_writ_block_inner_hash`, `writ_file_ends_with_newline`, `writ_rewrite_agents_md_with_inner`) verbatim — no forking, since they were already file-agnostic.
2. Added a `CLAUDE_MERGE_NOTE` variable distinct from `AGENTS_MERGE_NOTE`, per Gate 0's finding that the story's task list omitted the console-feedback wiring the spec's "no silent success" experience requirement demands.
3. Kept the apply-path call site bare (unwrapped) so `set -euo pipefail` still aborts the whole script on a malformed-marker error before `write_copy_manifest` runs — flagged by Gate 0 as a Medium-risk detail easy to get wrong.
4. Used the local variable name `claude_md` (not `agents_md`) inside `merge_claude_md` for naming hygiene, per Gate 0.

### Test Results

**Verification:** Story test suite + regression suite, both run directly against the real repo (not just self-reported).
**Coverage:** Branch/path coverage (no bash line-coverage tool — `bashcov`/`kcov` — available in this environment; adapted per spec-lite's testing guidance). All 7 decision-tree branches plus both explicit shadow-path gaps (empty-file input, missing-upstream-template) have an exercising test case.
- ✅ `scripts/tests/test_merge_claude_md.sh` — 9/9 scenarios passing
- ✅ `scripts/tests/test_merge_agents_md.sh` (regression) — all scenarios passing, no regression to shared helpers
- ✅ End-to-end verification against real fixture directories for all 5 AC (fresh install, no-marker append, malformed-marker abort, preserve-vs-force, dry-run truthfulness)

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration
- **Drift:** None
- **Security:** Clean (all variable expansions quoted, no `eval` on untrusted input, atomic `mktemp`+`mv` writes, no path traversal, no secrets)
- **Boundary Compliance:** Full — only Owned files (`scripts/install.sh`, `scripts/tests/test_merge_claude_md.sh`) modified/created; Readable files (`claude-code/CLAUDE.md`, `scripts/tests/test_merge_agents_md.sh`) untouched; `scripts/update.sh` (Story 2's scope) untouched.

### Deviations from Spec

None. The coding agent's one self-reported addition (an 8th/9th test case beyond the story's minimum of 6) is additive test coverage, not a contract deviation — review agent explicitly declined to log it as a DEV entry.

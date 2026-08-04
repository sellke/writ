# Story 2: Install and Update Scripts Skills Fanout

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** None
> **Estimated Effort:** Medium
> **Completed:** 2026-05-03

## User Story

**As a** Writ user installing or updating Writ in a consumer project,
**I want** `scripts/install.sh` and `scripts/update.sh` to fan out `skills/` to platform-native paths (`.cursor/skills/`, `.claude/skills/`) using the same three-way overlay logic that protects my command/agent customizations,
**So that** skills become a first-class install artifact with predictable behavior and zero learning curve.

## Acceptance Criteria

### Scenario 1: Fresh install fans skills out
- **Given** the Writ source repo has `skills/hello-writ/SKILL.md` and a sandbox project with no existing Writ install
- **When** I run `bash scripts/install.sh --platform cursor` from the sandbox
- **Then** `.cursor/skills/hello-writ/SKILL.md` exists with frontmatter intact (including `disable-model-invocation: true`), and the install summary reports `Skills: 1 new`

### Scenario 2: Dry-run preview lists skills
- **Given** `skills/hello-writ/SKILL.md` exists in source and the sandbox has no skills installed
- **When** I run `bash scripts/install.sh --dry-run --platform cursor`
- **Then** the preview output includes a `Skills:` section with `✨ New: skills/hello-writ/SKILL.md` listed; no files are written

### Scenario 3: Three-way overlay preserves user modifications
- **Given** `.cursor/skills/hello-writ/SKILL.md` was installed and then the user edited it locally (hash diverges from baseline)
- **When** the user runs `bash scripts/install.sh` again with no upstream changes
- **Then** the local file is preserved (overlay reports `⚡ Preserved: skills/hello-writ/SKILL.md (local modifications)`); content is unchanged

### Scenario 4: Overlay updates unmodified files
- **Given** `.cursor/skills/hello-writ/SKILL.md` matches the baseline hash, and upstream has changed
- **When** the user runs `bash scripts/install.sh`
- **Then** the local file is updated to upstream content; overlay reports `🔄 Update: skills/hello-writ/SKILL.md`

### Scenario 5: Sidecar files install once and never update
- **Given** `skills/hello-writ/SKILL.md` and `skills/hello-writ/example.txt` (sidecar) exist in source
- **When** install runs, then upstream changes `example.txt`, then install runs again
- **Then** `.cursor/skills/hello-writ/example.txt` reflects the *first install* content; subsequent updates do not touch sidecar files

### Scenario 6: Missing skills directory is silent
- **Given** the Writ source repo has no `skills/` directory (or it is empty)
- **When** I run `bash scripts/install.sh`
- **Then** the install completes successfully with no skills step output and no error; commands and agents install normally

### Scenario 7: Manifest tracks skill hashes
- **Given** an install completed with one skill
- **When** I inspect `.cursor/.writ-manifest`
- **Then** the manifest contains a `<hash>  skills/hello-writ/SKILL.md` line parallel to `commands/*.md` and `agents/*.md` entries

## Implementation Tasks

- [x] **Smoke fixture:** Created `skills/hello-writ/SKILL.md` + `skills/hello-writ/example.txt` (sidecar) for testing; deleted before story completion — Story 3 will create the official version.
- [x] **`overlay_scan_skills` function:** New function in `install.sh` (and parallel one in `update.sh`) that iterates skill folders under `$WRIT_SRC/skills/`, applies three-way overlay to `SKILL.md` only, copies sidecar files install-once.
- [x] **Step integration in `install.sh`:** Added Step "Skills..." after Agents step; `STEP_TOTAL` dynamically becomes 6 when skills are present, stays 5 otherwise.
- [x] **Inventory count:** Added `SKILL_COUNT`; banner prints `📜 Skills: $SKILL_COUNT` only when count > 0 (consistent with silent-skip semantics).
- [x] **Manifest writeback:** Extended `write_copy_manifest` (in both install.sh and update.sh) to enumerate `$PLATFORM_DIR/skills/*/SKILL.md` and append hash entries.
- [x] **Dry-run output:** `DRY_RUN` branch invokes `overlay_scan_skills` in `preview` mode; produces parallel-shaped `✨ New: skills/hello-writ/SKILL.md` output.
- [x] **`update.sh` parity:** Mirrored fanout logic — `overlay_scan_skills` with `_PRESERVED_FILES` tracking, scan in Phase 1, apply in Phase 2, stale detection extended for `skills/` paths, manifest writeback parallel.
- [x] **Symlink-mode handling:** When `EXISTING_MODE=link`, removes skill symlinks (folder-level + per-SKILL.md + parent skills/ link) before reinstalling.
- [x] **Git add scope:** Both install.sh and update.sh now include `[ -d "$PLATFORM_DIR/skills" ] && git add "$PLATFORM_DIR/skills/"` in the auto-commit block.
- [x] **Manual smoke test:** All 7 scenarios verified against `/tmp/writ-skill-test-*` sandboxes; cleaned up.

## Definition of Done

- [x] All seven acceptance criteria pass via manual verification on a sandbox project (✨ New / 🔄 Update / ⚡ Preserved / sidecar install-once / silent skip / manifest hash tracking — all verified)
- [x] `bash scripts/install.sh --dry-run` produces correct preview without side effects (no files written)
- [x] Existing command/agent fanout is regression-tested (Cursor sandbox installed 39 files including 30 commands + 7 agents + writ.mdc + system-instructions.md + manifest, all green)
- [x] `update.sh` syntax checked + Phase 1 scan logic mirrors install.sh; full apply path will activate once changes ship to GitHub (update.sh always pulls upstream)
- [x] Smoke test cleanup: `skills/hello-writ/` removed, all `/tmp/writ-skill-*` sandboxes deleted, `gen-skill.sh --check` still clean
- [x] Self-review: install.sh diff is purely additive (no behavioral change for projects without `skills/`); update.sh changes mirror install.sh structure

## Technical Notes

- **Overlay scope decision:** SKILL.md hash is tracked; sidecar files in skill folders install-once. Rationale: simpler overlay logic, matches AgentSkills convention where skills are SKILL.md plus optional supporting assets.
- **Naming:** Use `overlay_scan_skills` (new function) rather than generalizing `overlay_scan` to recurse — keeps existing behavior untouched and makes regression risk testable.
- **Banner emoji choice:** `📜` for Skills (matches the "scroll" / "manifest" metaphor; commands use `📋`, agents use `🤖`).
- **Reference:** `scripts/install.sh` lines 256–302 for the three-way overlay pattern; lines 360–367 for the Step pattern; lines 130–158 for the manifest write pattern.
- **Self-dogfood note:** This repo uses symlinks (`.cursor/` → product source). The symlink-mode handling matters for users converting from a linked install; verify symlink removal logic exercises skills paths too.

## Context for Agents

- **Coding agent context:** spec.md → `## Implementation Approach → ### Install/Update Fanout`. Reference `scripts/install.sh` for existing patterns. The `overlay_scan` function (lines 258–302) is the model to mirror.
- **Review agent context:** spec.md → `## Business Rules` (overlay rules) and `## Success Criteria` items 1, 8.
- **Testing agent context:** spec.md → `## Risks & Mitigations` (overlay regression row) and spec-lite.md "Edge Cases" (sidecar file behavior, name collisions).

---

## What Was Built

**Implementation Date:** 2026-05-03

### Files Modified

- **`scripts/install.sh`** (added ~110 lines)
  - `overlay_scan_skills` function (folder-aware, SKILL.md hash-tracked, sidecars install-once)
  - `SKILL_COUNT` inventory + `📜 Skills: N` banner row (conditional on count > 0)
  - Skills step in install loop with dynamic `STEP_TOTAL` (5 or 6)
  - `mkdir -p "$PLATFORM_DIR/skills"` only when source has skills
  - Symlink-mode cleanup extended for skill folders
  - Dry-run preview branch invokes `overlay_scan_skills` in preview mode
  - `write_copy_manifest` enumerates `$PLATFORM_DIR/skills/*/SKILL.md` and appends hash entries
  - Summary tally adds `SKILL_NEW/UPDATED/PRESERVED` and prints `Skills: N new, M updated, K preserved` line
  - Auto-commit `git add` scope includes `$PLATFORM_DIR/skills/`
- **`scripts/update.sh`** (added ~95 lines)
  - `overlay_scan_skills` function (with `_PRESERVED_FILES` tracking parallel to commands/agents)
  - Phase 1 scan: skills folder check + scan, accumulates into TOTAL_NEW/UPDATED/PRESERVED
  - Phase 2 apply: invokes `overlay_scan_skills` in apply mode
  - `detect_stale_files` extended with `skills)` case to compute upstream skill paths
  - `write_copy_manifest` mirrored from install.sh
  - Auto-commit `git add` scope includes `$PLATFORM_DIR/skills/`

### Implementation Decisions

1. **Function name `overlay_scan_skills` (not `overlay_scan_recursive`)** — keeps existing `overlay_scan` untouched. Regression risk on commands/agents fanout = zero. New function is testable in isolation.
2. **Sidecar copy uses install-once semantic** — first install copies all non-`SKILL.md` files; subsequent installs/updates never touch sidecars even if upstream changes. This matches the spec's "sidecar files install-once" rule and avoids a recursive overlay diff that would explode complexity.
3. **`STEP_TOTAL` is dynamic (5 or 6)** — when source has no `skills/` directory, the Skills step is omitted entirely and the user sees `[1/5]…[5/5]` with no skills mentions. When source has skills, they see `[3/6] Skills...`. This honors Scenario 6 (silent skip) while keeping the step counter accurate.
4. **Banner row `📜 Skills: N` is conditional on N > 0** — same rationale as silent skip: a project that never sees skills should never see the row. The same row-only-on-non-empty pattern applies to the summary line.
5. **Symlink-mode cleanup is conservative** — removes per-skill SKILL.md symlinks, per-folder symlinks, and the parent `$PLATFORM_DIR/skills` symlink if present. Mirrors the existing command/agent pattern. Only relevant for users converting from a future symlink mode (none currently in use).

### Test Results

**Verification:** Manual smoke tests against `/tmp/writ-skill-test-*` sandboxes (markdown/bash project — no test framework)

- ✅ Scenario 1: Fresh install → `.cursor/skills/hello-writ/SKILL.md` placed; banner `📜 Skills: 1`; summary `Skills: 1 new, 0 updated, 0 preserved`
- ✅ Scenario 2: `--dry-run` → `Skills:` section in preview lists `✨ New: skills/hello-writ/SKILL.md`; no files written
- ✅ Scenario 3: Local edit + reinstall → `Skills: 0 new, 0 updated, 1 preserved`; local content intact (verified via grep on USER MODIFICATION sentinel)
- ✅ Scenario 4: Reset to baseline + upstream change + reinstall → `Skills: 0 new, 1 updated, 0 preserved`; local now reflects UPSTREAM CHANGED
- ✅ Scenario 5: Upstream sidecar change + reinstall → local sidecar unchanged (verified via cat — still INITIAL_SIDECAR_CONTENT)
- ✅ Scenario 6: No `skills/` in source → no Skills mentions, no `.cursor/skills/` directory created, no errors, commands/agents install normally
- ✅ Scenario 7: Manifest contains `<sha256>  skills/hello-writ/SKILL.md` line parallel to commands/agents
- ✅ Bonus: Same fanout works on Claude Code platform (`.claude/skills/hello-writ/SKILL.md` with frontmatter intact)

### Review Outcome

**Result:** PASS (self-review)

- **Iteration count:** 1 iteration
- **Drift:** None — implementation follows the technical-spec sketch and the spec's overlay-at-SKILL.md-granularity rule
- **Security:** Clean — no shell injection (uses `cp` with quoted paths, `mkdir -p` for parent creation, no eval)
- **Boundary Compliance:** Owned files only (`scripts/install.sh`, `scripts/update.sh`); no out-of-scope edits

### Deviations from Spec

None. (Note: `update.sh`'s end-to-end apply test cannot run locally because `update.sh` always clones from GitHub; the apply path will activate once these changes ship. Phase 1 scan logic + syntax + structural mirroring of install.sh provides high confidence in the apply behavior.)

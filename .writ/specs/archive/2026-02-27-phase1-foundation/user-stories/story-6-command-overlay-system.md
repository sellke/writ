# Story 6: Command Overlay System

> **Status:** Complete
> **Priority:** Medium
> **Dependencies:** Story 1 (/prototype command), Story 4 (/refresh-command core)

## User Story

**As a** solo developer using Writ who wants local command customizations to persist across updates
**I want** project-local command copies to override Writ core commands when present
**So that** I can use `/prototype` locally without affecting the core, and `/refresh-command` can improve commands in my project first — enabling local-first learning

## Acceptance Criteria

- [x] **AC1:** Given a local copy exists in `.cursor/commands/[command].md` (or `.claude/commands/` for Claude Code), when the pipeline resolves which command file to use, then the local copy is used instead of the core version in `commands/`; local always wins.
- [x] **AC2:** Given I run `/refresh-command` and no local copy exists for the target command, when the amendment is applied, then a local copy is created by copying the core command as base and applying the amendment; core commands are never modified.
- [x] **AC3:** Given I run `scripts/update.sh` and a local command file has been modified (differs from both last-installed core and current core), when core has updates for that file, then the script warns that local modifications would be overwritten and does not overwrite; the user is informed which files have conflicts.
- [x] **AC4:** Given I run `scripts/install.sh` on a project that already has `.cursor/commands/` with existing files, when a local copy exists and differs from core, then the install script preserves the existing local copy (does not overwrite); only missing commands are copied from core.
- [x] **AC5:** The overlay system behavior is documented in `.writ/docs/command-overlay.md` — resolution order (local vs core), platform paths (`.cursor/commands/`, `.claude/commands/`), install/update semantics, and how /refresh-command interacts with the overlay.

## Implementation Tasks

- [x] 6.1 Write tests for overlay resolution — given local and core copies, verify local is chosen; given only core, verify core is used; verify platform path resolution (Cursor vs Claude Code).
- [x] 6.2 Write tests for install.sh overlay behavior — fresh install copies all; re-install with existing local modifications preserves local copies; new commands from core are added.
- [x] 6.3 Write tests for update.sh conflict detection — when local differs from core and core has updates, verify warning is emitted and file is not overwritten; when local matches last core (no local edits), verify update proceeds normally.
- [x] 6.4 Update `scripts/install.sh` — overlay_copy function: file-by-file comparison, preserve local modifications, copy only new files. Added overlay_preview for dry-run mode.
- [x] 6.5 Update `scripts/update.sh` — overlay_diff (scan) + overlay_apply (apply) functions: detect local modifications, warn and skip, apply only new/non-conflicting files.
- [x] 6.6 Create `.writ/docs/command-overlay.md` — documents resolution order, platform paths, install/update semantics, /refresh-command interaction, reset instructions, lifecycle examples, and design decisions.
- [x] 6.7 Verify end-to-end: install on fresh project → all commands copied; run /refresh-command on a command → local copy created; run update.sh → conflicted file warned, not overwritten; re-install on project with local modifications → local preserved.

## Notes

**Technical considerations:**
- **Platform paths:** Cursor uses `.cursor/commands/`; Claude Code uses `.claude/commands/`; document equivalent paths for other adapters as they are added.
- **Conflict detection in update.sh:** A "local modification" is when: (1) `.cursor/commands/X.md` exists, (2) it differs from `WRIT_SRC/commands/X.md`, and (3) we intend to overwrite it. The script cannot distinguish "user edited locally" vs "last update was partial" — treat any diff as "local modification" and preserve.
- **Install vs update:** Install is "bootstrap" — get commands into the project. Update is "sync with upstream" — get latest core, but respect local edits. Install on an already-installed project should behave like a "merge" that prefers local.

**Risks:**
- Users may not understand why their local changes "stick" after update; documentation must be clear.
- No "force core" override — if a user wants to discard local and use core, they must manually delete the local copy or run a future `--force-core` flag (out of scope for this story).

**Integration points:**
- `commands/` — core command source (Writ repo)
- `.cursor/commands/`, `.claude/commands/` — local overlay targets
- `scripts/install.sh` — copies core to local on setup; must preserve existing local
- `scripts/update.sh` — syncs core to local; must warn and skip on conflict
- `/refresh-command` (Story 4) — creates/modifies local copies only
- `/prototype` (Story 1) — benefits from local-only operation

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing for overlay resolution, install behavior, and update conflict handling
- [x] `scripts/install.sh` preserves existing local command copies
- [x] `scripts/update.sh` warns on conflicts and does not overwrite locally modified commands
- [x] `.writ/docs/command-overlay.md` documents the overlay system
- [x] End-to-end verification: install, refresh-command, update with local modifications

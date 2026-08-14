# Story 2: update.sh — migrate CLAUDE.md to inner-block hash tracking

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1 (introduces the `CLAUDE.md.writ-block` manifest key format this story reads/writes)

## User Story

**As a** developer running `bash update.sh --platform claude` (or `/update-writ`) in a project with an existing Writ installation
**I want to** `update.sh` to track `CLAUDE.md` via the same marker-block / inner-hash model `merge_agents_md` already uses, instead of comparing the whole file's hash to the raw upstream template
**So that** once Story 1 makes `install.sh` wrap `CLAUDE.md` content in `<!-- writ:start/end -->` markers, `update.sh` keeps correctly detecting unchanged/updated/preserved state — including cleanly upgrading a pre-fix installation's unmarked `CLAUDE.md` — instead of every future run silently regressing to "preserved (local modifications)" forever.

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.5

- [ ] Given no `CLAUDE.md` exists on disk, when `merge_claude_md` runs (preview then apply), then the action is `restore` and the applied file is created wrapped in `<!-- writ:start -->`/`<!-- writ:end -->` markers containing the upstream `claude-code/CLAUDE.md` content `[AC-2.1]`
- [ ] Given a pre-fix installation — a manifest with only the old bare `CLAUDE.md` whole-file-hash key (no `CLAUDE.md.writ-block` key) and a `CLAUDE.md` on disk with zero start/end markers — when `update.sh --platform claude` runs `merge_claude_md` for the first time after upgrading, then the outcome is `restore` (upstream block appended below the existing content, existing content fully preserved), never `error` `[AC-2.2]`
- [ ] Given `CLAUDE.md` exists with malformed markers (a count of start or end markers other than exactly one), when `merge_claude_md` runs, then the action is `error`, a `❌` line is printed, the function returns 13, and no write to `CLAUDE.md` occurs `[AC-2.3]`
- [ ] Given `CLAUDE.md` has well-formed markers whose inner-block hash equals the `CLAUDE.md.writ-block` manifest baseline (or `--force` is set), when `merge_claude_md apply` runs, then only the content between the markers is overwritten with the upstream inner content, everything outside the markers is byte-for-byte untouched, and `CLAUDE_MD_ACTION` feeds the same `update`-counted paths (`ACTIONABLE`, apply dispatch) that `AGENTS_MD_ACTION` uses today `[AC-2.4]`
- [ ] Given `CLAUDE.md` has well-formed markers whose inner-block hash matches neither the upstream template nor the manifest baseline, and `--force` is not set, when `merge_claude_md` runs, then the action is `preserved`, a warning line is printed, no overwrite occurs, and the file is added to `TOTAL_PRESERVED`/`ALL_PRESERVED_FILES` the same way a locally-modified `AGENTS.md` block is today `[AC-2.5]`

## Implementation Tasks

- [ ] 2.1 Write tests covering `update.sh`'s `merge_claude_md` decision tree — file absent (restore), pre-fix upgrade (old bare-`CLAUDE.md`-key manifest + unmarked file on disk → restore, not error), malformed markers (error, return 13, no write), well-formed + baseline/force match (update, inner-only overwrite), well-formed + upstream match (unchanged), well-formed + neither match without `--force` (preserved) — mirroring the structure of `scripts/tests/test_merge_agents_md.sh` `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`
- [ ] 2.2 Implement `merge_claude_md` in `update.sh`, structurally parallel to the existing `merge_agents_md` (`update.sh:318-407`), operating on `CLAUDE.md` / `$WRIT_SRC/claude-code/CLAUDE.md` and reusing `writ_block_marker_counts`, `writ_compute_writ_block_inner_hash`, `writ_file_ends_with_newline`, `hash_file`, and `manifest_hash_for("CLAUDE.md.writ-block")` — do not write new parallel helpers `[AC-2.1, AC-2.2, AC-2.3, AC-2.4]`
- [ ] 2.3 Replace the whole-file-hash `CLAUDE_MD_ACTION` block (`update.sh:840-864`) with a call to `merge_claude_md preview` under the `elif [ "$PLATFORM" = "claude" ]` branch, wiring `CLAUDE_MD_ACTION`/its note into `TOTAL_PRESERVED`/`ALL_PRESERVED_FILES` the same way `AGENTS_MD_ACTION` is wired at `update.sh:868-874` `[AC-2.2, AC-2.5]`
- [ ] 2.4 Update the `ACTIONABLE` count logic (`update.sh:886-887`) so the claude branch counts `CLAUDE_MD_ACTION` in `{update, restore}` — the old `{update, new}` check no longer matches, since `merge_claude_md`'s decision tree reports `restore` (not `new`) for both the absent-file and no-markers cases `[AC-2.1, AC-2.2, AC-2.4]`
- [ ] 2.5 Replace the apply-phase conditional `cp` (`update.sh:975`) with a call to `merge_claude_md apply` when `CLAUDE_MD_ACTION` is `update` or `restore`, mirroring how `update.sh:980-981` calls `merge_agents_md apply` for `AGENTS_MD_ACTION` `[AC-2.1, AC-2.2, AC-2.4]`
- [ ] 2.6 Manually verify the pre-fix upgrade scenario end-to-end: construct a manifest with only the bare `CLAUDE.md` key (no `CLAUDE.md.writ-block`) plus an unmarked `CLAUDE.md` on disk, run `update.sh --platform claude`, and confirm the block is appended with zero content loss and no `error`/malformed misclassification `[AC-2.2]`
- [ ] 2.7 Run the new/updated test suite and confirm every case in the decision tree (restore-absent, restore-no-markers/pre-fix-upgrade, error-malformed, update, unchanged, preserved) passes `[AC-2.1, AC-2.3, AC-2.4, AC-2.5]`

## Notes

- **Keep-synced duplication:** `update.sh` has no shared sourcing with `install.sh` (both are standalone, curl-pipeable scripts), so `merge_claude_md` here is a structurally-identical, separately-maintained copy of Story 1's `install.sh` version — comment it "keep synced," matching the existing `merge_agents_md` convention across both files.
- **Manifest key migration is the crux of the upgrade edge case:** an old manifest only has the bare `CLAUDE.md` (whole-file hash) key; `manifest_hash_for("CLAUDE.md.writ-block")` on such a manifest must return empty/absent, not accidentally fall back to the old key's value — that's what routes the pre-fix case into "no markers found → restore" (case 2) rather than a false match or a false `error`.
- **`ACTIONABLE` check needs a real behavior change, not just a rename:** today's check is `{update, new}` because the old logic could only ever say `new` (file absent) or `update`/`preserved` (file present). `merge_claude_md` collapses both "absent" and "no markers found" into a single `restore` action (per `merge_agents_md`'s own convention), so the count check must change to `{update, restore}` — reusing the old `{update, new}` check verbatim would silently stop counting the restore case as actionable.
- **Integration with Story 1:** this story is a pure consumer of the `CLAUDE.md.writ-block` manifest key Story 1's `install.sh` changes introduce (via `write_copy_manifest`). No `install.sh` changes happen in this story.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [Malformed CLAUDE.md markers] — spec.md → 🎯 Experience Design → Error experience
- **Shadow paths:** [Pre-fix installation upgrading via update.sh] — spec.md → 📋 Business Rules (detailed) → Manifest migration
- **Business rules:** [One shared manifest key `CLAUDE.md.writ-block` retiring the bare `CLAUDE.md` key, `--force` always overwrites the inner block, content outside markers never touched, malformed markers are always an error, pre-fix unmarked file treated as "existing without markers" not malformed] — spec.md → Specification Contract → 📋 Business Rules, and → 📋 Business Rules (detailed) → Decision tree
- **Experience:** [Per-file console feedback lines — ✨ Restored, 🔄 Updated, ⚡ Preserved with warning, ❌ malformed-markers error with non-zero exit] — spec.md → 🎯 Experience Design → Feedback model / Error experience

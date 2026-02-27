# Command Overlay System

The overlay system ensures that **local command customizations always win** over Writ core commands. When a project has a local copy of a command file, that copy is what the IDE resolves — not the core version in `commands/`. This enables `/refresh-command` to improve commands locally without affecting core, and protects local customizations from being overwritten by `install.sh` or `update.sh`.

## Resolution Order

When the IDE (Cursor, Claude Code) resolves a command, it looks at the **local copy first**:

```
┌─────────────────────────────────────────────────────────┐
│  User invokes /prototype                                │
│                                                         │
│  1. Check local:  .cursor/commands/prototype.md         │
│     └─ EXISTS? ──▶ Use this. Done.                      │
│                                                         │
│  2. Check core:   commands/prototype.md                 │
│     └─ EXISTS? ──▶ Use this. Done.                      │
│                                                         │
│  3. Neither? ──▶ Command not found.                     │
└─────────────────────────────────────────────────────────┘
```

**Local always wins.** If `.cursor/commands/prototype.md` exists, the core `commands/prototype.md` is never consulted for that invocation.

## Platform Paths

| Platform    | Local command directory       | Local agent directory       |
|-------------|-------------------------------|-----------------------------|
| Cursor      | `.cursor/commands/`           | `.cursor/agents/`           |
| Claude Code | `.claude/commands/`           | `.claude/agents/`           |

The install and update scripts target `.cursor/` by default. Claude Code users can adapt paths as needed — the overlay principle is the same regardless of platform.

## How Files Flow

```
                    ┌──────────────────┐
                    │   Writ Core      │
                    │   commands/*.md   │
                    │   agents/*.md     │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
         install.sh     update.sh    /refresh-command
              │              │              │
              ▼              ▼              ▼
     ┌─────────────────────────────────────────────┐
     │         Local Project                        │
     │  .cursor/commands/*.md  (what the IDE uses)  │
     │  .cursor/agents/*.md                         │
     └─────────────────────────────────────────────┘
```

Each pathway respects the overlay rule: **never overwrite a locally modified file without explicit user action**.

## Install Behavior (`scripts/install.sh`)

Install is the bootstrap step — it gets Writ commands into a project for the first time.

### Fresh Install (no `.cursor/commands/` exists)

All core commands and agents are copied to the local directory. This is identical to pre-overlay behavior.

### Re-Install (`.cursor/commands/` already exists)

For each file in core:

| Condition | Action |
|-----------|--------|
| Local copy exists AND **differs** from core | **Preserved** — local modifications kept, file not overwritten |
| Local copy exists AND **matches** core | **Unchanged** — no action needed |
| Local copy does not exist | **Copied** — new command added from core |

The summary reports how many files were preserved, copied, or unchanged. Example output:

```
✅ Writ installed!

  📋 Overlay summary:
     Commands — 1 new
     Commands — 2 preserved (local modifications kept)
     Agents   — 1 preserved (local modifications kept)

  💡 To reset a file to core: delete the local copy and re-run install.
```

### Dry Run

`bash install.sh --dry-run` previews overlay behavior without making changes — showing which files would be preserved, copied, or left unchanged.

## Update Behavior (`scripts/update.sh`)

Update syncs the project with the latest Writ core while respecting local edits.

### Phase 1: Scan

For each file in the latest core:

| Condition | Report |
|-----------|--------|
| Local copy does not exist | `✨ New: commands/foo.md` |
| Local copy exists AND **differs** from core | `⚠️ Skipped: commands/foo.md — local modifications detected` |
| Local copy exists AND **matches** core | Nothing reported (already up to date) |

### Phase 2: Apply

Only non-conflicting files are touched:
- **New files**: Copied from core
- **Locally modified files**: Skipped (preserved)
- **Identical files**: No action

### Conflict Summary

After applying, the update script lists all skipped files:

```
✅ Writ updated! (2 file(s) changed)

  ⚠️  3 file(s) with local modifications were preserved:
    commands/prototype.md
    commands/refresh-command.md
    agents/coding-agent.md

  💡 To reset a file to core: delete the local copy and re-run update.
```

### Important Limitation

The update script cannot distinguish between:
1. **User edited locally** — the user customized the file (should skip)
2. **Stale copy** — the local file matches an older core version that has since been updated (user might want the update)

Both cases result in "local file differs from current core," and the script conservatively **preserves** the local copy. If you want the latest core version of a specific file, delete the local copy and re-run the update.

## `/refresh-command` Interaction

`/refresh-command` is the primary way local command copies diverge from core. Here's how it works:

1. **No local copy exists**: `/refresh-command` copies the core command as a base, then applies amendments on top — creating the local copy.
2. **Local copy exists**: Amendments are applied directly to the local copy. The core command is never touched.
3. **Core is read-only**: `/refresh-command` never modifies files in `commands/`. All learning stays in `.cursor/commands/` until explicitly promoted.

This means after running `/refresh-command`, the local copy will differ from core — and subsequent `install.sh` or `update.sh` runs will correctly preserve it.

## Resetting to Core

To discard local modifications and return to the core version of a command:

```bash
# Reset a single command
rm .cursor/commands/prototype.md
bash scripts/install.sh --no-commit

# Reset all commands (nuclear option)
rm .cursor/commands/*.md
bash scripts/install.sh --no-commit
```

After deleting the local copy, the next install or update will copy the current core version.

## Lifecycle Example

```
Day 1: Fresh install
  install.sh → copies commands/prototype.md → .cursor/commands/prototype.md

Day 3: User runs /refresh-command on prototype
  /refresh-command → amends .cursor/commands/prototype.md
  Now: .cursor/commands/prototype.md ≠ commands/prototype.md

Day 5: User runs update.sh
  update.sh → detects local modification on prototype.md → SKIPS
  New command added from core: .cursor/commands/new-command.md → COPIED
  Result: local prototype.md preserved, new command added

Day 7: User wants latest core prototype.md
  rm .cursor/commands/prototype.md
  bash scripts/update.sh → copies current core prototype.md
```

## Rules & System Instructions

`writ.mdc` (rules) and `system-instructions.md` are **always updated** by both install and update scripts — they don't follow overlay semantics. These files are framework infrastructure, not user-customizable commands.

## Design Decisions

**Why not track a manifest of installed checksums?**
A manifest (recording the checksum of each file at install time) would let the update script distinguish "user edited" from "stale copy." This was considered but deferred — the conservative "preserve on any diff" approach is simpler, predictable, and safe. A manifest-based approach may be added in a future story if the "stale copy" problem becomes common.

**Why not support `--force-core` to overwrite local?**
Explicit deletion (`rm` + re-install) is simple, visible, and leaves no ambiguity about what happened. A force flag could be added later if the manual workflow proves too cumbersome.

# Reinstall Writ Command (reinstall-writ)

## Overview

Remove all Writ platform files and install fresh from the latest upstream release. This is the nuclear option — all local modifications to commands, agents, and rules are discarded. Use when your installation is in a bad state or you want a clean slate without manual cleanup.

**When to use:** Local files are corrupted, heavily diverged from upstream, or you just want to start fresh. For selective updates that preserve your customizations, use `/update-writ` instead.

## Invocation

| Invocation | Behavior |
|---|---|
| `/reinstall-writ` | Full removal + fresh install with confirmation gate |

---

## Command Process

### Step 1: Detect Installation

Same detection logic as `/update-writ` Step 1 — read the manifest to determine platform, version, and mode.

**Locate manifest:**
```bash
cat .cursor/.writ-manifest 2>/dev/null
cat .claude/.writ-manifest 2>/dev/null
```

**Guards:**

| Condition | Action |
|---|---|
| No manifest found | Warn but allow — user may be reinstalling over a broken state. Prompt for platform selection instead. |
| Running in Writ source repo | Abort — "This is the Writ source repository." |

If no manifest is found, ask which platform to target:

```
AskQuestion({
  title: "Platform Selection",
  questions: [{
    id: "platform",
    prompt: "No Writ manifest found. Which platform should we install for?",
    options: [
      { id: "cursor", label: "Cursor (.cursor/)" },
      { id: "claude", label: "Claude Code (.claude/)" }
    ]
  }]
})
```

**Platform paths** — same table as `/update-writ` Step 1.

### Step 2: Confirm Destructive Operation

This command destroys local modifications. Gate it behind explicit confirmation.

**Inventory current installation** — count files that will be removed:

```bash
ls [platform_dir]/commands/*.md | wc -l
ls [platform_dir]/agents/*.md | wc -l
```

**Check for customized files** — if a manifest exists, compare local hashes to baseline hashes. Count files where the hashes differ (these have local modifications that will be lost).

```
AskQuestion({
  title: "Confirm Reinstall",
  questions: [{
    id: "confirm",
    prompt: "This will remove and reinstall all Writ files.\n\n  Platform: [Cursor/Claude Code]\n  Files to remove: [N] commands, [M] agents, rules/manifest\n  Customized files that will be lost: [K]\n\n  .writ/ directory will NOT be touched.\n\nProceed?",
    options: [
      { id: "yes", label: "Yes — remove everything and install fresh" },
      { id: "abort", label: "Cancel — keep current installation" },
      { id: "update", label: "Use /update-writ instead — preserve my customizations" }
    ]
  }]
})
```

- **yes** → continue to Step 3
- **abort** → stop
- **update** → advise running `/update-writ` and stop

### Step 3: Remove Platform Files

Delete all Writ-managed files from the platform directory.

**Files to remove:**
- `[platform_dir]/commands/*.md` — all command files
- `[platform_dir]/agents/*.md` — all agent files
- Platform-specific extras:
  - Cursor: `[platform_dir]/rules/writ.mdc`, `[platform_dir]/system-instructions.md`
  - Claude Code: `CLAUDE.md` (project root)
- `[platform_dir]/.writ-manifest`

**Do NOT remove:**
- `.writ/` directory and all its contents (specs, docs, ADRs, state)
- Any non-Writ files in the platform directory
- The platform directory itself (other tools may use it)
- `.gitignore` entries

Handle symlinks gracefully — if any file is a symlink, remove the symlink (not the target).

### Step 4: Install Fresh from Upstream

```bash
WRIT_SRC=$(mktemp -d)
git clone --depth 1 https://github.com/sellke/writ.git "$WRIT_SRC"
```

**Copy all files** — this is equivalent to `install.sh --force`:

1. `mkdir -p [platform_dir]/commands [platform_dir]/agents`
2. Copy all commands: `cp $WRIT_SRC/commands/*.md [platform_dir]/commands/`
3. Copy all agents: `cp $WRIT_SRC/[agents_src]/*.md [platform_dir]/agents/`
4. Copy platform-specific files:
   - Cursor: `cp $WRIT_SRC/cursor/writ.mdc [platform_dir]/rules/` and `cp $WRIT_SRC/system-instructions.md [platform_dir]/`
   - Claude Code: `cp $WRIT_SRC/claude-code/CLAUDE.md ./CLAUDE.md`
5. Write fresh manifest with baselines for every installed file

### Step 5: Git Commit

```bash
git add [platform_dir]/commands/ [platform_dir]/agents/ [manifest_file]
# Plus platform-specific files
git commit -m "chore: reinstall Writ (clean slate from [version])"
```

### Step 6: Cleanup and Summary

Remove the temporary clone.

```
✅ Writ reinstalled! (version: [hash])

  📋 Installed: [N] commands, [M] agents
  📜 Platform: [Cursor/Claude Code]

  All files are now at upstream defaults.
  Local modifications have been discarded.

  .writ/ directory was not touched — your specs,
  docs, and ADRs are intact.
```

---

## Error Handling

| Condition | Response |
|---|---|
| Network failure | Abort — don't leave a half-removed state. If removal already happened, report what was removed and instruct user to run `install.sh` manually. |
| Clone succeeds but copy fails | Report which files failed, attempt cleanup |
| No git repo | Skip commit step, warn user |

**Critical safety:** If the clone fails *after* files have been removed (Step 3 completed but Step 4 fails), the installation is broken. Report this clearly and provide recovery instructions:

```
❌ Reinstall failed — upstream clone failed after removal.

Your Writ files have been removed but new ones could not be installed.
To recover, run from your terminal:

  bash <(curl -s https://raw.githubusercontent.com/sellke/writ/main/scripts/install.sh) --platform [platform]
```

---

## Integration with Writ

| Command | Relationship |
|---------|-------------|
| `install.sh` | First-time installation and recovery path if `/reinstall-writ` fails mid-operation |
| `/update-writ` | Selective update that preserves customizations — use this when you don't need a clean slate |
| `/uninstall-writ` | Removal without reinstallation |

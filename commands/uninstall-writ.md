# Uninstall Writ Command (uninstall-writ)

## Overview

Remove Writ from the project. Deletes all platform files — commands, agents, rules, and the manifest — but leaves the `.writ/` directory intact so your specs, ADRs, docs, and research are preserved.

**When to use:** You're done with Writ and want to remove it from the project. Your work artifacts in `.writ/` stay unless you delete them manually.

## Invocation

| Invocation | Behavior |
|---|---|
| `/uninstall-writ` | Remove Writ platform files with confirmation |

---

## Command Process

### Step 1: Detect Installation

Read the manifest to determine platform and scope.

```bash
cat .cursor/.writ-manifest 2>/dev/null
cat .claude/.writ-manifest 2>/dev/null
cat .codex/.writ-manifest 2>/dev/null
```

**If multiple manifests exist** (multi-platform installation), ask which to uninstall:

```
AskQuestion({
  title: "Platform Selection",
  questions: [{
    id: "platform",
    prompt: "Writ is installed for multiple platforms. Which should we uninstall?",
    options: [
      { id: "cursor", label: "Cursor (.cursor/)" },
      { id: "claude", label: "Claude Code (.claude/)" },
      { id: "codex", label: "Codex CLI (.codex/, AGENTS.md, .agents/skills/)" },
      { id: "all", label: "All platforms — remove Writ from Cursor, Claude Code, and Codex CLI" }
    ]
  }]
})
```

**If no manifest found** — check for Writ files anyway (commands/agents directories with `.md` files in the platform dir, or `.toml` files for Codex agents). If found, proceed with a warning that no manifest exists. If nothing found, report "Writ doesn't appear to be installed" and stop.

**Guard:** If running in the Writ source repo, abort.

### Step 2: Inventory and Confirm

Scan the files that will be removed and present a summary.

**Count files:**
```bash
ls [platform_dir]/commands/*.md 2>/dev/null | wc -l
ls [platform_dir]/agents/*.md 2>/dev/null | wc -l
```

**Check for customizations** — if manifest exists, count files where local hash differs from baseline.

```
AskQuestion({
  title: "Confirm Uninstall",
  questions: [{
    id: "confirm",
    prompt: "This will remove Writ from your project.\n\n  Platform: [Cursor/Claude Code/Codex CLI]\n  Removing: [N] commands, [M] agents, platform extras, manifest\n  Customized files: [K] (will be lost)\n\n  Keeping: .writ/ directory (specs, docs, ADRs)\n\nCodex CLI: AGENTS.md will be modified by removing only the Writ block, and .codex/config.toml removal will be prompted separately by uninstall.sh because the file is install-once and user-owned. See adapters/codex.md.\n\nProceed?",
    options: [
      { id: "yes", label: "Yes — remove Writ" },
      { id: "abort", label: "Cancel" }
    ]
  }]
})
```

### Step 3: Remove Files

Delete Writ-managed files. Run per-platform if "all" was selected.

**Remove in order:**

1. **Commands:** `rm [platform_dir]/commands/*.md`
2. **Agents:** `rm [platform_dir]/agents/*.md` for Cursor/Claude Code, or `rm .codex/agents/*.toml` for Codex CLI
3. **Platform-specific files:**
   - Cursor: `rm [platform_dir]/rules/writ.mdc [platform_dir]/system-instructions.md`
   - Claude Code: `rm CLAUDE.md`
   - Codex CLI: remove only the marker-bounded Writ block from `AGENTS.md`; prompt before removing `.codex/config.toml`; remove Writ-installed skills from `.agents/skills/`
4. **Manifest:** `rm [platform_dir]/.writ-manifest`

**Clean up empty directories** — if `commands/` or `agents/` directories are now empty, remove them. Don't remove the platform directory itself (`.cursor/`, `.claude/`, or `.codex/`) unless it becomes empty.

**Do NOT remove:**
- `.writ/` directory
- `.gitignore` entries (harmless to leave)
- Any non-`.md` files in commands/ or agents/ directories
- The platform directory itself
- Codex CLI: user content outside the `<!-- writ:start -->` / `<!-- writ:end -->` markers in `AGENTS.md`; `.codex/config.toml` unless the user confirms removal

### Step 4: Git Commit

```bash
git add -u [platform_dir]/
# Plus CLAUDE.md for Claude Code or AGENTS.md for Codex CLI
git commit -m "chore: uninstall Writ ([platform_label])"
```

Use `git add -u` to stage deletions without adding untracked files.

### Step 5: Summary

```
✅ Writ has been removed.

  🗑  Removed: [N] commands, [M] agents, rules, manifest
  📂 Kept: .writ/ directory (specs, docs, ADRs intact)

  To reinstall later:
    bash <(curl -s https://raw.githubusercontent.com/sellke/writ/main/scripts/install.sh) --platform [platform]

  Codex CLI reinstall:
    bash <(curl -s https://raw.githubusercontent.com/sellke/writ/main/scripts/install.sh) --platform codex

  To also remove .writ/:
    rm -rf .writ
```

Codex note: `uninstall.sh --platform codex` removes only the Writ block from `AGENTS.md` and prompts before removing `.codex/config.toml`. See [`adapters/codex.md`](../adapters/codex.md) for the AGENTS.md ownership convention.

---

## Error Handling

| Condition | Response |
|---|---|
| No manifest and no Writ files | "Writ doesn't appear to be installed." |
| Source repo detected | Abort |
| Partial removal failure | Report which files couldn't be removed, suggest manual cleanup |
| No git repo | Skip commit step |

---

## Integration with Writ

| Command | Relationship |
|---------|-------------|
| `install.sh` | Reinstallation path after uninstall |
| `/reinstall-writ` | Remove + reinstall in one step (use when you want Writ back immediately) |
| `/update-writ` | Use instead if you want to keep Writ but refresh it |
| `uninstall.sh` | Non-interactive terminal counterpart |

---

## References

- Standing instructions: [`commands/_preamble.md`](_preamble.md)
- Identity & Prime Directive: [`system-instructions.md`](../system-instructions.md)

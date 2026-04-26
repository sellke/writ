# Update Writ Command (update-writ)

## Overview

Pull the latest Writ release from upstream and interactively decide what to do with files you've customized. Unlike `update.sh` (which silently preserves all local modifications), this command presents each customized file and lets you choose — overwrite, keep, or diff — so you stay in control of what changes.

**When to use:** You want the latest commands, agents, and rules from upstream but have customized some files and want per-file control over what gets overwritten.

## Invocation

| Invocation | Behavior |
|---|---|
| `/update-writ` | Interactive update with per-file customization prompts |

---

## Command Process

### Step 1: Detect Installation

Read the manifest to determine what's installed and how.

**Locate manifest:**
```bash
# Check both platforms — use whichever exists
cat .cursor/.writ-manifest 2>/dev/null
cat .claude/.writ-manifest 2>/dev/null
```

**Extract from manifest header:**
- `mode` — must be `copy` (linked installations must run `unlink.sh` first)
- `platform` — `cursor` or `claude`
- `version` — current installed version hash
- `source` — upstream repo URL

**Parse file baselines:** Each non-comment, non-empty line is `<sha256>  <relative-path>`. Build a lookup of baseline hashes keyed by relative path.

**Guards:**

| Condition | Action |
|---|---|
| No manifest found | Abort — "Writ doesn't appear to be installed. Run `install.sh` first." |
| `mode: link` | Abort — "Linked installation detected. Run `unlink.sh` to convert to copies, then re-run `/update-writ`." |
| Running in Writ source repo (SKILL.md + commands/ + agents/ + scripts/ all exist) | Abort — "This is the Writ source repository. `/update-writ` is for updating Writ in other projects." |

**Platform-specific paths:**

| Platform | Platform dir | Commands src | Agents src | Extra files |
|---|---|---|---|---|
| `cursor` | `.cursor` | `commands` | `agents` | `rules/writ.mdc`, `system-instructions.md` |
| `claude` | `.claude` | `commands` | `claude-code/agents` | `CLAUDE.md` (project root) |

### Step 2: Fetch Latest Upstream

```bash
WRIT_SRC=$(mktemp -d)
git clone --depth 1 https://github.com/sellke/writ.git "$WRIT_SRC"
```

Extract the new version: `git -C "$WRIT_SRC" log -1 --format="%h %s"`.

If the clone fails, abort with a network error message and clean up the temp directory.

### Step 3: Three-Way Scan

For every `.md` file in upstream `commands/` and the platform's agents source directory, classify it against the local installation:

**Hash each file** using SHA-256 (`shasum -a 256`).

**Classification logic per file:**

```
upstream_hash = hash(upstream file)
local_hash    = hash(local file)       — if local file exists
baseline_hash = manifest entry         — if entry exists for this path

if local file doesn't exist:
  → NEW (will be added)

if local_hash == upstream_hash:
  → UNCHANGED (skip)

if baseline_hash is empty:
  → CUSTOMIZED (no baseline — conservatively assume modified)

if local_hash == baseline_hash:
  → UPDATED (local matches baseline — safe to overwrite)

if local_hash != baseline_hash AND local_hash != upstream_hash:
  → CUSTOMIZED (local was modified by user)
```

**Apply same logic to platform-specific files:**
- Cursor: `rules/writ.mdc`, `system-instructions.md` (upstream sources: `cursor/writ.mdc`, `system-instructions.md`)
- Claude Code: `CLAUDE.md` (upstream source: `claude-code/CLAUDE.md`)

**Detect stale files** — files present in the manifest but removed upstream. If the local hash matches the baseline (user didn't modify it), mark for removal. If modified, flag but don't auto-remove.

### Step 4: Present Summary

Display the scan results grouped by action:

```
⚡ Writ Update Scan
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Installed: abc1234
  Latest:    def5678 — "Add /update-writ command"

  ✨ New:        3 file(s)
  🔄 Updated:   5 file(s) — safe to overwrite (unmodified locally)
  ⚡ Customized: 2 file(s) — you've made local changes
  🗑  Stale:     1 file(s) — removed upstream
  ✅ Unchanged:  15 file(s)
```

If everything is unchanged, report "Already up to date!" and stop.

### Step 5: Handle Customized Files

If customized files exist, present them one at a time or as a batch depending on count.

**For 1–5 customized files — per-file AskQuestion:**

```
AskQuestion({
  title: "Customized File: commands/implement-story.md",
  questions: [{
    id: "action_implement_story",
    prompt: "This file has local modifications. What should we do?",
    options: [
      { id: "keep", label: "Keep my version — don't overwrite" },
      { id: "overwrite", label: "Overwrite with upstream — discard my changes" },
      { id: "diff", label: "Show diff first — then decide" }
    ]
  }]
})
```

If the user picks "diff," show a unified diff between local and upstream, then re-ask with keep/overwrite only.

**For 6+ customized files — batch AskQuestion:**

```
AskQuestion({
  title: "Customized Files (N files)",
  questions: [{
    id: "batch_action",
    prompt: "N files have local modifications:\n- commands/foo.md\n- commands/bar.md\n- ...\n\nWhat should we do?",
    options: [
      { id: "keep_all", label: "Keep all my versions" },
      { id: "overwrite_all", label: "Overwrite all with upstream" },
      { id: "per_file", label: "Decide per file" }
    ]
  }]
})
```

### Step 6: Apply Changes

Apply in this order:

1. **New files** — copy from upstream
2. **Updated files** — overwrite (local was unmodified)
3. **Customized files** — apply per user decision from Step 5
4. **Stale files** — remove unmodified stale files; skip modified stale files with a warning
5. **Platform-specific files** — same three-way logic as commands/agents

### Step 7: Regenerate Manifest

Write a new manifest with updated baselines for all installed files:

```
# Writ Manifest — do not edit manually
# Tracks installed file baselines for safe overlay updates.
# mode: copy
# platform: [cursor|claude]
# version: [new version hash]
# date: [ISO 8601 UTC timestamp]
# source: https://github.com/sellke/writ.git
<sha256>  commands/create-spec.md
<sha256>  commands/implement-story.md
...
```

Every currently installed file gets a fresh hash entry — including files the user chose to keep (their current hash becomes the new baseline).

### Step 8: Git Commit

If the project is a git repo:

```bash
git add [platform_dir]/commands/ [platform_dir]/agents/ [manifest_file]
# Plus platform-specific files (rules/writ.mdc, system-instructions.md, or CLAUDE.md)
git commit -m "chore: update Writ ([old_version] → [new_version])"
```

### Step 9: Cleanup and Summary

Remove the temporary clone directory.

```
✅ Writ updated! (abc1234 → def5678)

  ✨ 3 new file(s) installed
  🔄 5 file(s) updated
  ⚡ 2 file(s) preserved (local modifications kept)
  🗑  1 file(s) removed (stale)

  💡 Preserved files keep your local changes. To reset any file
     to upstream, delete it and run /update-writ again.
```

---

## Error Handling

| Condition | Response |
|---|---|
| Network failure (clone fails) | Abort with message, clean up temp dir |
| No manifest | "Writ is not installed. Run install.sh first." |
| Linked installation | "Run unlink.sh first to convert to copies." |
| Writ source repo detected | "This command is for installed projects, not the source repo." |
| No git repo | Skip git commit step, warn user |

---

## Integration with Writ

| Command | Relationship |
|---------|-------------|
| `install.sh` | First-time installation — `/update-writ` handles subsequent updates |
| `update.sh` | Non-interactive terminal counterpart — silently preserves all local modifications |
| `unlink.sh` | Must run before `/update-writ` if installation uses symlinks |
| `/reinstall-writ` | Nuclear option — removes everything and installs fresh (no three-way merge) |
| `/uninstall-writ` | Removes Writ entirely |
| `/status` | Could surface "Writ update available" in future iterations |

---

## References

- Standing instructions: [`commands/_preamble.md`](_preamble.md)
- Identity & Prime Directive: [`system-instructions.md`](../system-instructions.md)

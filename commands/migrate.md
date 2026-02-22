# Migrate Command (migrate)

## Overview

Migrate an existing Code Captain project to Writ. Renames directories, updates references, preserves all specs, stories, ADRs, research, and state. Zero data loss.

## What Changes

| Before | After | Content |
|---|---|---|
| `.code-captain/` | `.writ/` | Specs, stories, ADRs, research, docs — all preserved |
| `.code-captain/specs/` | `.writ/specs/` | Every spec folder, story file, and sub-spec intact |
| `.code-captain/decision-records/` | `.writ/decision-records/` | All ADRs preserved |
| `.code-captain/research/` | `.writ/research/` | All research preserved |
| `.code-captain/state/` | `.writ/state/` | Workflow state (can be cleaned) |
| `.cursor/commands/*.md` | `.claude/commands/*.md` or `.cursor/commands/*.md` | Replaced with Writ versions |
| `.cursor/agents/*.md` | `.claude/agents/*.md` or `.cursor/agents/*.md` | Replaced with Writ agents |
| `system-instructions.md` | Updated | Writ identity and tool references |
| References to `.code-captain/` in files | Updated to `.writ/` | Spec files, stories, sub-specs |

## What Does NOT Change

- **Spec content** — your contracts, requirements, scope boundaries
- **Story files** — user stories, acceptance criteria, implementation tasks, status
- **Sub-specs** — technical specs, API specs, database schemas, wireframes
- **ADRs** — all architectural decisions preserved
- **Research** — all research outputs preserved
- **Git history** — migration is a simple rename + commit
- **Story progress** — completed/in-progress status preserved exactly

## Modes

| Invocation | Behavior |
|---|---|
| `/migrate` | Interactive — scans project, shows plan, asks confirmation |
| `/migrate --dry-run` | Preview only — show what would change, touch nothing |
| `/migrate --yes` | Auto-confirm — run migration without prompting |
| `/migrate --platform cursor` | Stay on Cursor (`.cursor/commands/` + `.cursor/agents/`) |
| `/migrate --platform claude-code` | Use Claude Code native (`.claude/commands/` + `.claude/agents/`) |

## Command Process

### Phase 1: Scan & Validate

#### Step 1.1: Detect Code Captain Installation

```bash
# Check for Code Captain artifacts
CC_DIR=""
if [ -d ".code-captain" ]; then
  CC_DIR=".code-captain"
elif [ -d "code-captain" ]; then
  CC_DIR="code-captain"
fi

# Check for existing Writ (abort if already migrated)
if [ -d ".writ" ]; then
  echo "⚠️ .writ/ already exists. This project may already be migrated."
  echo "If this is a partial migration, run /migrate --force to continue."
  exit 1
fi

# Inventory what exists
echo "Scanning Code Captain installation..."
SPECS=$(find $CC_DIR/specs -maxdepth 1 -type d 2>/dev/null | wc -l)
STORIES=$(find $CC_DIR/specs -name "story-*.md" 2>/dev/null | wc -l)
ADRS=$(find $CC_DIR/decision-records -name "*.md" 2>/dev/null | wc -l)
RESEARCH=$(find $CC_DIR/research -name "*.md" 2>/dev/null | wc -l)
DOCS=$(find $CC_DIR/docs -name "*.md" 2>/dev/null | wc -l)
ISSUES=$(find $CC_DIR/issues -name "*.md" 2>/dev/null | wc -l)
```

#### Step 1.2: Detect Platform

```bash
# What platform is currently installed?
PLATFORM="unknown"
if [ -d ".cursor/commands" ] || [ -d ".cursor/agents" ]; then
  PLATFORM="cursor"
fi
if [ -d ".claude/commands" ] || [ -d ".claude/agents" ]; then
  PLATFORM="claude-code"
fi
```

#### Step 1.3: Present Migration Plan

```
📦 Code Captain → Writ Migration Plan

Found Code Captain at: .code-captain/

Inventory:
  📋 Specifications:      3 specs
  📝 User Stories:        14 stories (9 completed, 3 in progress, 2 not started)
  📐 Decision Records:    5 ADRs
  🔍 Research:            2 documents
  📚 Documentation:       4 files
  🎫 Issues:              7 issues
  ⚙️  State files:         2 execution states

Current platform: Cursor

Migration steps:
  1. Rename .code-captain/ → .writ/
  2. Update internal references (.code-captain → .writ) in:
     - Spec files, story files, README files, sub-specs
  3. Install Writ commands (replace .cursor/commands/)
  4. Install Writ agents (replace .cursor/agents/)
  5. Update system-instructions.md
  6. Update .gitignore (if present)
  7. Commit migration

No data will be deleted. This is a rename + upgrade.
```

```
AskQuestion({
  title: "Migration",
  questions: [
    {
      id: "proceed",
      prompt: "Ready to migrate?",
      options: [
        { id: "yes", label: "Run migration" },
        { id: "dry_run", label: "Dry run first (show changes, don't apply)" },
        { id: "platform", label: "Change target platform before migrating" },
        { id: "abort", label: "Cancel" }
      ]
    }
  ]
})
```

---

### Phase 2: Execute Migration

#### Step 2.1: Rename Directory

```bash
# The core migration — simple rename
mv .code-captain .writ

# If there was a code-captain/ (no dot), handle that too
if [ -d "code-captain" ]; then
  mv code-captain .writ
fi
```

#### Step 2.2: Update Internal References

```bash
# Find all markdown files in .writ/ that reference the old path
find .writ -name "*.md" -exec sed -i 's|\.code-captain/|.writ/|g' {} +
find .writ -name "*.md" -exec sed -i 's|\.code-captain|.writ|g' {} +
find .writ -name "*.md" -exec sed -i 's|code-captain/|writ/|g' {} +

# Also in JSON state files
find .writ -name "*.json" -exec sed -i 's|\.code-captain|.writ|g' {} +

# Update any references in project root files
for f in README.md CLAUDE.md CONTRIBUTING.md; do
  if [ -f "$f" ]; then
    sed -i 's|\.code-captain/|.writ/|g' "$f"
    sed -i 's|\.code-captain|.writ|g' "$f"
    sed -i 's|Code Captain|Writ|g' "$f"
  fi
done
```

#### Step 2.3: Preserve Spec Integrity

**Verify no spec content was corrupted by the rename:**

```bash
# Count files before and after (should match exactly)
STORIES_AFTER=$(find .writ/specs -name "story-*.md" 2>/dev/null | wc -l)
if [ "$STORIES" != "$STORIES_AFTER" ]; then
  echo "❌ Story count mismatch! Before: $STORIES, After: $STORIES_AFTER"
  echo "Rolling back..."
  mv .writ .code-captain
  exit 1
fi

# Verify story status is preserved (spot check)
for story in .writ/specs/*/user-stories/story-*.md; do
  if grep -q "Status:.*Completed" "$story"; then
    echo "✅ $(basename $story) — Completed status preserved"
  fi
done
```

#### Step 2.4: Install Writ Commands

**For Cursor:**
```bash
mkdir -p .cursor/commands .cursor/agents

# Remove old Code Captain commands
rm -f .cursor/commands/*.md

# Install Writ commands
cp path/to/writ/commands/*.md .cursor/commands/

# Install Writ agents
rm -f .cursor/agents/*.md
cp path/to/writ/agents/*.md .cursor/agents/

# Update system instructions
cp path/to/writ/system-instructions.md .cursor/system-instructions.md
```

**For Claude Code:**
```bash
mkdir -p .claude/commands .claude/agents

# Install Writ commands
cp path/to/writ/commands/*.md .claude/commands/

# Install native subagent definitions (see adapters/claude-code.md)
# These are the proper .claude/agents/ files with YAML frontmatter
# writ-architect.md, writ-coder.md, writ-reviewer.md, etc.

# Create/update CLAUDE.md (see adapters/claude-code.md for template)
```

#### Step 2.5: Update .gitignore

```bash
if [ -f .gitignore ]; then
  # Replace old entries
  sed -i 's|\.code-captain/state/|.writ/state/|g' .gitignore
  sed -i 's|\.code-captain|.writ|g' .gitignore
  
  # Add .writ/state/ if not present
  if ! grep -q ".writ/state" .gitignore; then
    echo "" >> .gitignore
    echo "# Writ ephemeral state" >> .gitignore
    echo ".writ/state/" >> .gitignore
  fi
fi
```

#### Step 2.6: Commit Migration

```bash
git add -A
git commit -m "chore: migrate Code Captain → Writ

Renamed .code-captain/ → .writ/
Updated all internal references.
Installed Writ commands and agents.
All specs, stories, ADRs, and research preserved.

No content was modified — this is a rename + tooling upgrade.
See: https://github.com/sellke/writ"
```

---

### Phase 3: Verification

#### Step 3.1: Integrity Check

```
✅ Migration Complete: Code Captain → Writ

Verified:
  📋 Specifications:      3 specs (✅ all intact)
  📝 User Stories:        14 stories (✅ all intact, statuses preserved)
     - 9 Completed ✅
     - 3 In Progress
     - 2 Not Started
  📐 Decision Records:    5 ADRs (✅ all intact)
  🔍 Research:            2 documents (✅ all intact)
  📚 Documentation:       4 files (✅ all intact)
  🎫 Issues:              7 issues (✅ all intact)

Commands installed:    18 (including new: /implement-story, /refactor, /release, /security-audit)
Agents installed:      6 (architecture-check, coding, review, testing, documentation, story-gen)
Platform:              Cursor / Claude Code

Internal references updated: X files
Git commit:            ✅ Created

Your specs, stories, and all project history are exactly where you left them.
Just use /writ commands instead of /code-captain commands going forward.
```

#### Step 3.2: What's New

```
🆕 New in Writ (you didn't have these in Code Captain):

  /implement-story   — Multi-agent SDLC pipeline with 6 quality gates
                       (replaces /execute-task)
  /refactor          — Scoped refactoring with verification
                       (replaces /swab)
  /release           — Automated changelog, versioning, GitHub releases
  /security-audit    — 5-phase security analysis with auto-fix
  /verify-spec       — 8-check comprehensive validation
                       (upgraded from basic README sync)

  New agents:
  - Architecture Check — reviews approach BEFORE coding
  - Persistent memory — reviewer learns your codebase patterns

Run /status to see your project through Writ's eyes.
```

---

## Rollback

If anything goes wrong:

```bash
# Undo the directory rename
mv .writ .code-captain

# Restore old commands (from git)
git checkout -- .cursor/commands/ .cursor/agents/

# Undo the commit
git reset HEAD~1
```

---

## Migration Script (One-Liner)

For quick migration without the interactive flow:

```bash
# Backup, rename, update refs, commit
mv .code-captain .writ && \
find .writ -name "*.md" -exec sed -i 's|\.code-captain|.writ|g' {} + && \
find .writ -name "*.json" -exec sed -i 's|\.code-captain|.writ|g' {} + && \
git add -A && \
git commit -m "chore: migrate Code Captain → Writ"
```

Then install Writ commands/agents separately (see platform-specific adapter docs).

## FAQ

**Q: Will my completed stories still show as completed?**
A: Yes. Story status is in the story file header (`> **Status:** Completed ✅`). Migration doesn't touch content — only the directory name and path references change.

**Q: Will my in-progress work be affected?**
A: No. If you're mid-implementation, your story files, task checkboxes, and progress tracking all carry over. Just continue with `/implement-story` instead of `/execute-task`.

**Q: What about my .code-captain/docs/ (tech-stack, code-style)?**
A: Moved to `.writ/docs/` automatically. All project context files preserved.

**Q: Can I keep both for a while?**
A: Not recommended (creates confusion), but you could symlink: `ln -s .writ .code-captain` if you need backwards compatibility temporarily.

**Q: What if I have custom commands I wrote with /new-command?**
A: They'll be in `.cursor/commands/` or `.code-captain/commands/`. The migration copies Writ's commands but won't delete unrecognized custom commands if they're in `.cursor/commands/`. Check after migration and update any `.code-captain` references in your custom commands to `.writ`.

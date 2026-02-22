#!/bin/bash
# Writ Migration Script — Code Captain → Writ
# Run from your project root: bash path/to/migrate.sh
#
# Flags:
#   --dry-run    Preview changes without applying
#   --yes        Skip confirmation prompt
#   --no-commit  Don't auto-commit after migration

set -euo pipefail

DRY_RUN=false
AUTO_YES=false
NO_COMMIT=false

for arg in "$@"; do
  case $arg in
    --dry-run)  DRY_RUN=true ;;
    --yes)      AUTO_YES=true ;;
    --no-commit) NO_COMMIT=true ;;
    --help|-h)
      echo "Usage: bash migrate.sh [--dry-run] [--yes] [--no-commit]"
      echo ""
      echo "Migrates Code Captain (.code-captain/) to Writ (.writ/)"
      echo "Run from your project root."
      exit 0
      ;;
  esac
done

echo "⚡ Writ Migration — Code Captain → Writ"
echo "========================================="
echo ""

# Detect Code Captain
CC_DIR=""
if [ -d ".code-captain" ]; then
  CC_DIR=".code-captain"
elif [ -d "code-captain" ]; then
  CC_DIR="code-captain"
else
  echo "❌ No .code-captain/ or code-captain/ directory found."
  echo "   Run this from your project root."
  exit 1
fi

# Check for existing .writ
if [ -d ".writ" ]; then
  echo "⚠️  .writ/ already exists. Already migrated?"
  exit 1
fi

# Inventory
SPECS=$(find "$CC_DIR/specs" -maxdepth 1 -mindepth 1 -type d 2>/dev/null | wc -l | tr -d ' ')
STORIES=$(find "$CC_DIR/specs" -name "story-*.md" 2>/dev/null | wc -l | tr -d ' ')
COMPLETED=$(grep -rl "Status:.*Completed" "$CC_DIR/specs" 2>/dev/null | wc -l | tr -d ' ')
IN_PROGRESS=$(grep -rl "Status:.*In Progress" "$CC_DIR/specs" 2>/dev/null | wc -l | tr -d ' ')
NOT_STARTED=$(grep -rl "Status:.*Not Started" "$CC_DIR/specs" 2>/dev/null | wc -l | tr -d ' ')
ADRS=$(find "$CC_DIR/decision-records" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
RESEARCH=$(find "$CC_DIR/research" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
ISSUES=$(find "$CC_DIR/issues" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')

echo "Found: $CC_DIR/"
echo ""
echo "  📋 Specifications:    $SPECS"
echo "  📝 User Stories:      $STORIES"
echo "     ✅ Completed:      $COMPLETED"
echo "     🔄 In Progress:    $IN_PROGRESS"
echo "     ⬜ Not Started:    $NOT_STARTED"
echo "  📐 Decision Records:  $ADRS"
echo "  🔍 Research:          $RESEARCH"
echo "  🎫 Issues:            $ISSUES"
echo ""

# Detect platform
PLATFORM="none"
if [ -d ".cursor/commands" ] || [ -d ".cursor/agents" ]; then
  PLATFORM="cursor"
fi

# Count files that reference old paths
REF_COUNT=$(grep -rl "\.code-captain\|code-captain/" "$CC_DIR" 2>/dev/null | wc -l | tr -d ' ')
echo "  📎 Files with internal references to update: $REF_COUNT"
echo "  🔧 Current platform: $PLATFORM"
echo ""

if [ "$DRY_RUN" = true ]; then
  echo "🏃 DRY RUN — No changes will be made"
  echo ""
  echo "Would do:"
  echo "  1. mv $CC_DIR → .writ/"
  echo "  2. Update $REF_COUNT files: .code-captain → .writ"
  echo "  3. Update .gitignore (if present)"
  echo "  4. Git commit"
  echo ""
  echo "Run without --dry-run to execute."
  exit 0
fi

if [ "$AUTO_YES" = false ]; then
  echo "This will:"
  echo "  1. Rename $CC_DIR/ → .writ/"
  echo "  2. Update all internal path references"
  echo "  3. Commit the migration"
  echo ""
  echo "All content (specs, stories, ADRs) is preserved. No data is deleted."
  echo ""
  read -p "Proceed? [y/N] " -n 1 -r
  echo ""
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
  fi
fi

echo ""
echo "Migrating..."

# Step 1: Rename
echo "  [1/4] Renaming $CC_DIR/ → .writ/"
mv "$CC_DIR" .writ

# Step 2: Update references in all markdown and JSON files
echo "  [2/4] Updating internal references..."
find .writ -name "*.md" -exec sed -i 's|\.code-captain/|.writ/|g' {} + 2>/dev/null || true
find .writ -name "*.md" -exec sed -i 's|\.code-captain|.writ|g' {} + 2>/dev/null || true
find .writ -name "*.json" -exec sed -i 's|\.code-captain|.writ|g' {} + 2>/dev/null || true

# Update root-level files
for f in README.md CLAUDE.md CONTRIBUTING.md; do
  if [ -f "$f" ]; then
    sed -i 's|\.code-captain/|.writ/|g' "$f" 2>/dev/null || true
    sed -i 's|\.code-captain|.writ|g' "$f" 2>/dev/null || true
  fi
done

# Update .cursor files if present
if [ -d ".cursor" ]; then
  find .cursor -name "*.md" -exec sed -i 's|\.code-captain/|.writ/|g' {} + 2>/dev/null || true
  find .cursor -name "*.md" -exec sed -i 's|\.code-captain|.writ|g' {} + 2>/dev/null || true
fi

# Step 3: Update .gitignore
echo "  [3/4] Updating .gitignore..."
if [ -f .gitignore ]; then
  sed -i 's|\.code-captain/state/|.writ/state/|g' .gitignore 2>/dev/null || true
  sed -i 's|\.code-captain|.writ|g' .gitignore 2>/dev/null || true
fi

if [ -f .gitignore ] && ! grep -q ".writ/state" .gitignore 2>/dev/null; then
  echo "" >> .gitignore
  echo "# Writ ephemeral state" >> .gitignore
  echo ".writ/state/" >> .gitignore
fi

# Step 4: Verify
echo "  [4/4] Verifying..."
STORIES_AFTER=$(find .writ/specs -name "story-*.md" 2>/dev/null | wc -l | tr -d ' ')
COMPLETED_AFTER=$(grep -rl "Status:.*Completed" .writ/specs 2>/dev/null | wc -l | tr -d ' ')

if [ "$STORIES" != "$STORIES_AFTER" ]; then
  echo ""
  echo "  ❌ Story count mismatch! Before: $STORIES, After: $STORIES_AFTER"
  echo "  Rolling back..."
  mv .writ "$CC_DIR"
  echo "  Rolled back. Migration failed."
  exit 1
fi

echo ""
echo "✅ Migration complete!"
echo ""
echo "  Stories:    $STORIES_AFTER (all preserved)"
echo "  Completed:  $COMPLETED_AFTER (statuses intact)"
echo ""

# Commit
if [ "$NO_COMMIT" = false ]; then
  if command -v git &> /dev/null && [ -d .git ]; then
    git add -A
    git commit -m "chore: migrate Code Captain → Writ

Renamed .code-captain/ → .writ/
Updated all internal path references.
All specs, stories, ADRs, and research preserved.

See: https://github.com/sellke/writ"
    echo "  📦 Git commit created."
  fi
fi

echo ""
echo "Next steps:"
echo "  1. Install Writ commands: copy writ/commands/*.md to .cursor/commands/"
echo "  2. Install Writ agents:   copy writ/agents/*.md to .cursor/agents/"
echo "  3. Run /status to see your project through Writ"
echo ""
echo "⚡ Gawd issues writs. The framework executes them."

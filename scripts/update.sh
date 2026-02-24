#!/bin/bash
# Writ Updater — pulls latest writ and syncs .cursor/ files
# Run from your project root: bash <(curl -s https://raw.githubusercontent.com/sellke/writ/main/scripts/update.sh)
#
# Flags:
#   --dry-run    Preview changes without applying
#   --no-commit  Don't auto-commit after update

set -euo pipefail

DRY_RUN=false
NO_COMMIT=false

for arg in "$@"; do
  case $arg in
    --dry-run)    DRY_RUN=true ;;
    --no-commit)  NO_COMMIT=true ;;
    --help|-h)
      echo "Usage: bash update.sh [--dry-run] [--no-commit]"
      echo ""
      echo "Updates Writ commands, agents, and rules from latest GitHub release."
      echo "Run from your project root."
      exit 0
      ;;
  esac
done

echo "⚡ Writ Updater"
echo "================"
echo ""

# Verify writ is installed
if [ ! -d ".cursor/commands" ] || [ ! -f ".cursor/rules/writ.mdc" ]; then
  echo "❌ Writ doesn't appear to be installed in this project."
  echo "   Run install.sh first."
  exit 1
fi

# Clone latest
echo "📥 Fetching latest writ..."
WRIT_SRC=$(mktemp -d)
git clone --depth 1 https://github.com/sellke/writ.git "$WRIT_SRC" 2>/dev/null
trap "rm -rf $WRIT_SRC" EXIT

VERSION=$(cd "$WRIT_SRC" && git log -1 --format="%h %s")
echo "   Latest: $VERSION"
echo ""

# Diff check
CHANGES=0
for f in "$WRIT_SRC/commands/"*.md; do
  fname=$(basename "$f")
  if [ -f ".cursor/commands/$fname" ]; then
    if ! diff -q "$f" ".cursor/commands/$fname" > /dev/null 2>&1; then
      echo "  📝 Updated:  commands/$fname"
      CHANGES=$((CHANGES + 1))
    fi
  else
    echo "  ✨ New:      commands/$fname"
    CHANGES=$((CHANGES + 1))
  fi
done

for f in "$WRIT_SRC/agents/"*.md; do
  fname=$(basename "$f")
  if [ -f ".cursor/agents/$fname" ]; then
    if ! diff -q "$f" ".cursor/agents/$fname" > /dev/null 2>&1; then
      echo "  📝 Updated:  agents/$fname"
      CHANGES=$((CHANGES + 1))
    fi
  else
    echo "  ✨ New:      agents/$fname"
    CHANGES=$((CHANGES + 1))
  fi
done

if ! diff -q "$WRIT_SRC/cursor/writ.mdc" ".cursor/rules/writ.mdc" > /dev/null 2>&1; then
  echo "  📝 Updated:  rules/writ.mdc"
  CHANGES=$((CHANGES + 1))
fi

if [ -f ".cursor/system-instructions.md" ] && ! diff -q "$WRIT_SRC/system-instructions.md" ".cursor/system-instructions.md" > /dev/null 2>&1; then
  echo "  📝 Updated:  system-instructions.md"
  CHANGES=$((CHANGES + 1))
elif [ ! -f ".cursor/system-instructions.md" ]; then
  echo "  ✨ New:      system-instructions.md"
  CHANGES=$((CHANGES + 1))
fi

echo ""

if [ "$CHANGES" -eq 0 ]; then
  echo "✅ Already up to date!"
  exit 0
fi

echo "  $CHANGES file(s) to update"
echo ""

if [ "$DRY_RUN" = true ]; then
  echo "🏃 DRY RUN — No changes applied."
  exit 0
fi

# Apply updates
echo "Updating..."
cp "$WRIT_SRC/commands/"*.md .cursor/commands/
cp "$WRIT_SRC/agents/"*.md .cursor/agents/
cp "$WRIT_SRC/cursor/writ.mdc" .cursor/rules/
cp "$WRIT_SRC/system-instructions.md" .cursor/

echo ""
echo "✅ Writ updated! ($CHANGES files changed)"

# Commit
if [ "$NO_COMMIT" = false ]; then
  if command -v git &> /dev/null && [ -d .git ]; then
    git add -A
    git commit -m "chore: update Writ to latest ($VERSION)

Updated $CHANGES file(s) from https://github.com/sellke/writ" 2>/dev/null && echo "  📦 Git commit created." || echo "  ℹ️  Nothing to commit."
  fi
fi

echo ""
echo "⚡ So it is written. So it shall be built."

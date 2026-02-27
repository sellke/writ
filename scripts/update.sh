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

# --- Overlay-aware diff & update ---
# For each file: detect if local has modifications (differs from core).
# If local is modified, the user customized it — skip and warn.
# If local matches core (or doesn't exist), safe to update/add.
UPDATES=0
SKIPPED=0
NEW=0
SKIPPED_FILES=""

overlay_diff() {
  local src_dir="$1"
  local local_dir="$2"
  local label="$3"

  for src_file in "$src_dir"/*.md; do
    [ -f "$src_file" ] || continue
    local fname
    fname=$(basename "$src_file")
    local local_file="$local_dir/$fname"

    if [ ! -f "$local_file" ]; then
      echo "  ✨ New:       $label/$fname"
      NEW=$((NEW + 1))
    elif ! diff -q "$src_file" "$local_file" > /dev/null 2>&1; then
      echo "  ⚠️  Skipped:  $label/$fname — local modifications detected"
      SKIPPED=$((SKIPPED + 1))
      SKIPPED_FILES="$SKIPPED_FILES    $label/$fname\n"
    fi
  done
}

overlay_apply() {
  local src_dir="$1"
  local local_dir="$2"

  for src_file in "$src_dir"/*.md; do
    [ -f "$src_file" ] || continue
    local fname
    fname=$(basename "$src_file")
    local local_file="$local_dir/$fname"

    if [ ! -f "$local_file" ]; then
      cp "$src_file" "$local_file"
      UPDATES=$((UPDATES + 1))
    elif diff -q "$src_file" "$local_file" > /dev/null 2>&1; then
      : # identical — nothing to do
    else
      : # local modifications — already warned, skip
    fi
  done
}

# Phase 1: Scan for changes
echo "Scanning for changes..."
echo ""

overlay_diff "$WRIT_SRC/commands" ".cursor/commands" "commands"
overlay_diff "$WRIT_SRC/agents" ".cursor/agents" "agents"

RULE_CHANGED=false
if ! diff -q "$WRIT_SRC/cursor/writ.mdc" ".cursor/rules/writ.mdc" > /dev/null 2>&1; then
  echo "  📝 Updated:  rules/writ.mdc"
  RULE_CHANGED=true
fi

SYSINST_CHANGED=false
if [ -f ".cursor/system-instructions.md" ] && ! diff -q "$WRIT_SRC/system-instructions.md" ".cursor/system-instructions.md" > /dev/null 2>&1; then
  echo "  📝 Updated:  system-instructions.md"
  SYSINST_CHANGED=true
elif [ ! -f ".cursor/system-instructions.md" ]; then
  echo "  ✨ New:      system-instructions.md"
  SYSINST_CHANGED=true
fi

TOTAL_ACTIONABLE=$((NEW))
[ "$RULE_CHANGED" = true ] && TOTAL_ACTIONABLE=$((TOTAL_ACTIONABLE + 1))
[ "$SYSINST_CHANGED" = true ] && TOTAL_ACTIONABLE=$((TOTAL_ACTIONABLE + 1))

echo ""

if [ "$TOTAL_ACTIONABLE" -eq 0 ] && [ "$SKIPPED" -eq 0 ]; then
  echo "✅ Already up to date!"
  exit 0
fi

# Nothing to update, but some files were preserved
if [ "$TOTAL_ACTIONABLE" -eq 0 ] && [ "$SKIPPED" -gt 0 ]; then
  echo "✅ Already up to date!"
  echo ""
  echo "  ⚠️  $SKIPPED file(s) with local modifications were preserved:"
  printf "$SKIPPED_FILES"
  echo ""
  echo "  💡 To reset a file to core: delete the local copy and re-run update."
  exit 0
fi

echo "  $TOTAL_ACTIONABLE file(s) to update"
if [ "$SKIPPED" -gt 0 ]; then
  echo "  $SKIPPED file(s) skipped (local modifications preserved)"
fi
echo ""

if [ "$DRY_RUN" = true ]; then
  echo "🏃 DRY RUN — No changes applied."
  if [ "$SKIPPED" -gt 0 ]; then
    echo ""
    echo "  Files with local modifications (would be skipped):"
    printf "$SKIPPED_FILES"
    echo ""
    echo "  💡 To reset a file to core: delete the local copy and re-run update."
  fi
  exit 0
fi

# Phase 2: Apply updates (only non-conflicting files)
echo "Updating..."
overlay_apply "$WRIT_SRC/commands" ".cursor/commands"
overlay_apply "$WRIT_SRC/agents" ".cursor/agents"

[ "$RULE_CHANGED" = true ] && cp "$WRIT_SRC/cursor/writ.mdc" .cursor/rules/ && UPDATES=$((UPDATES + 1))
[ "$SYSINST_CHANGED" = true ] && cp "$WRIT_SRC/system-instructions.md" .cursor/ && UPDATES=$((UPDATES + 1))

echo ""
echo "✅ Writ updated! ($UPDATES file(s) changed)"

if [ "$SKIPPED" -gt 0 ]; then
  echo ""
  echo "  ⚠️  $SKIPPED file(s) with local modifications were preserved:"
  printf "$SKIPPED_FILES"
  echo ""
  echo "  💡 To reset a file to core: delete the local copy and re-run update."
fi

# Commit
if [ "$NO_COMMIT" = false ]; then
  if command -v git &> /dev/null && [ -d .git ]; then
    git add -A
    git commit -m "chore: update Writ to latest ($VERSION)

Updated $UPDATES file(s) from https://github.com/sellke/writ" 2>/dev/null && echo "  📦 Git commit created." || echo "  ℹ️  Nothing to commit."
  fi
fi

echo ""
echo "⚡ So it is written. So it shall be built."

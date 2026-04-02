#!/bin/bash
# Writ Uninstaller — removes Writ commands, agents, rules, and manifest
# Run from your project root: bash <(curl -s https://raw.githubusercontent.com/sellke/writ/main/scripts/uninstall.sh)
#
# Removes platform files only. The .writ/ directory (specs, docs, ADRs) is preserved.
#
# Flags:
#   --dry-run      Preview changes without applying
#   --no-commit    Don't auto-commit after removal
#   --platform     Target platform: cursor (default) or claude
#   --include-writ Also remove the .writ/ directory (destructive)

set -euo pipefail

DRY_RUN=false
NO_COMMIT=false
PLATFORM=""
INCLUDE_WRIT=false

while [ $# -gt 0 ]; do
  case $1 in
    --dry-run)       DRY_RUN=true ;;
    --no-commit)     NO_COMMIT=true ;;
    --include-writ)  INCLUDE_WRIT=true ;;
    --platform)
      shift
      PLATFORM="${1:-}"
      if [ "$PLATFORM" != "cursor" ] && [ "$PLATFORM" != "claude" ]; then
        echo "❌ Unknown platform: $PLATFORM"
        echo "   Supported: cursor, claude"
        exit 1
      fi
      ;;
    --help|-h)
      echo "Usage: bash uninstall.sh [--dry-run] [--no-commit] [--platform cursor|claude] [--include-writ]"
      echo ""
      echo "Removes Writ commands, agents, rules, and manifest from your project."
      echo "Run from your project root."
      echo ""
      echo "Platforms:"
      echo "  cursor (default)  Remove from .cursor/"
      echo "  claude            Remove from .claude/"
      echo ""
      echo "Flags:"
      echo "  --dry-run       Preview changes without applying"
      echo "  --no-commit     Don't auto-commit after removal"
      echo "  --include-writ  Also remove the .writ/ directory (specs, docs, ADRs — destructive)"
      exit 0
      ;;
    *)
      echo "Unknown option: $1 (try --help)"
      exit 1
      ;;
  esac
  shift
done

# ---------------------------------------------------------------------------
# Guards
# ---------------------------------------------------------------------------

if [ -f "SKILL.md" ] && [ -d "commands" ] && [ -d "agents" ] && [ -d "scripts" ]; then
  echo "❌ This appears to be the Writ source repository."
  echo "   uninstall.sh is for removing Writ from other projects."
  exit 1
fi

# ---------------------------------------------------------------------------
# Auto-detect platform if not specified
# ---------------------------------------------------------------------------

if [ -z "$PLATFORM" ]; then
  HAS_CURSOR=false
  HAS_CLAUDE=false
  [ -f ".cursor/.writ-manifest" ] && HAS_CURSOR=true
  [ -f ".claude/.writ-manifest" ] && HAS_CLAUDE=true

  if [ "$HAS_CURSOR" = true ] && [ "$HAS_CLAUDE" = true ]; then
    echo "❌ Multiple Writ installations detected (.cursor/ and .claude/)."
    echo "   Specify which to remove: --platform cursor or --platform claude"
    echo "   Run twice to remove both."
    exit 1
  elif [ "$HAS_CURSOR" = true ]; then
    PLATFORM="cursor"
  elif [ "$HAS_CLAUDE" = true ]; then
    PLATFORM="claude"
  else
    # No manifest — check for Writ files anyway
    if [ -d ".cursor/commands" ] && ls .cursor/commands/*.md &>/dev/null; then
      PLATFORM="cursor"
      echo "  ⚠️  No manifest found but Writ files detected in .cursor/"
    elif [ -d ".claude/commands" ] && ls .claude/commands/*.md &>/dev/null; then
      PLATFORM="claude"
      echo "  ⚠️  No manifest found but Writ files detected in .claude/"
    else
      echo "❌ Writ doesn't appear to be installed in this project."
      echo "   No manifest or Writ files found in .cursor/ or .claude/"
      exit 1
    fi
  fi
fi

# ---------------------------------------------------------------------------
# Platform-specific paths
# ---------------------------------------------------------------------------

if [ "$PLATFORM" = "cursor" ]; then
  PLATFORM_DIR=".cursor"
  PLATFORM_LABEL="Cursor"
elif [ "$PLATFORM" = "claude" ]; then
  PLATFORM_DIR=".claude"
  PLATFORM_LABEL="Claude Code"
fi

echo "⚡ Writ Uninstaller ($PLATFORM_LABEL)"
echo "==================="
echo ""

# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------

CMD_COUNT=0
AGENT_COUNT=0
EXTRA_FILES=()

for f in "$PLATFORM_DIR"/commands/*.md; do
  [ -f "$f" ] && CMD_COUNT=$((CMD_COUNT + 1))
done

for f in "$PLATFORM_DIR"/agents/*.md; do
  [ -f "$f" ] && AGENT_COUNT=$((AGENT_COUNT + 1))
done

if [ "$PLATFORM" = "cursor" ]; then
  [ -f "$PLATFORM_DIR/rules/writ.mdc" ] && EXTRA_FILES+=("$PLATFORM_DIR/rules/writ.mdc")
  [ -f "$PLATFORM_DIR/system-instructions.md" ] && EXTRA_FILES+=("$PLATFORM_DIR/system-instructions.md")
elif [ "$PLATFORM" = "claude" ]; then
  [ -f "CLAUDE.md" ] && EXTRA_FILES+=("CLAUDE.md")
fi

HAS_MANIFEST=false
[ -f "$PLATFORM_DIR/.writ-manifest" ] && HAS_MANIFEST=true

echo "  Files to remove:"
echo "    📋 Commands:  $CMD_COUNT"
echo "    🤖 Agents:    $AGENT_COUNT"
echo "    📄 Extras:    ${#EXTRA_FILES[@]} (${EXTRA_FILES[*]:-none})"
[ "$HAS_MANIFEST" = true ] && echo "    📌 Manifest:  1"
echo ""

if [ "$INCLUDE_WRIT" = true ] && [ -d ".writ" ]; then
  WRIT_FILE_COUNT=$(find .writ -type f 2>/dev/null | wc -l | tr -d ' ')
  echo "  ⚠️  --include-writ: Also removing .writ/ ($WRIT_FILE_COUNT files)"
  echo "     This includes specs, docs, ADRs, and all work artifacts."
  echo ""
fi

TOTAL=$((CMD_COUNT + AGENT_COUNT + ${#EXTRA_FILES[@]}))
[ "$HAS_MANIFEST" = true ] && TOTAL=$((TOTAL + 1))

if [ "$TOTAL" -eq 0 ]; then
  echo "  Nothing to remove."
  exit 0
fi

# ---------------------------------------------------------------------------
# Dry run
# ---------------------------------------------------------------------------

if [ "$DRY_RUN" = true ]; then
  echo "🏃 DRY RUN — No changes will be made"
  echo ""
  for f in "$PLATFORM_DIR"/commands/*.md; do
    [ -f "$f" ] && echo "  🗑  $f"
  done
  for f in "$PLATFORM_DIR"/agents/*.md; do
    [ -f "$f" ] && echo "  🗑  $f"
  done
  for f in "${EXTRA_FILES[@]}"; do
    echo "  🗑  $f"
  done
  [ "$HAS_MANIFEST" = true ] && echo "  🗑  $PLATFORM_DIR/.writ-manifest"
  if [ "$INCLUDE_WRIT" = true ] && [ -d ".writ" ]; then
    echo "  🗑  .writ/ (entire directory)"
  fi
  echo ""
  echo "  Would remove $TOTAL file(s)."
  echo "  .writ/ directory would be $([ "$INCLUDE_WRIT" = true ] && echo "REMOVED" || echo "preserved")."
  exit 0
fi

# ---------------------------------------------------------------------------
# Remove
# ---------------------------------------------------------------------------

echo "Removing..."
REMOVED=0

for f in "$PLATFORM_DIR"/commands/*.md; do
  if [ -f "$f" ] || [ -L "$f" ]; then
    rm -f "$f"
    REMOVED=$((REMOVED + 1))
  fi
done

# Remove commands dir if empty
rmdir "$PLATFORM_DIR/commands" 2>/dev/null || true

for f in "$PLATFORM_DIR"/agents/*.md; do
  if [ -f "$f" ] || [ -L "$f" ]; then
    rm -f "$f"
    REMOVED=$((REMOVED + 1))
  fi
done

# Remove agents dir if empty
rmdir "$PLATFORM_DIR/agents" 2>/dev/null || true

for f in "${EXTRA_FILES[@]}"; do
  rm -f "$f"
  REMOVED=$((REMOVED + 1))
done

if [ "$HAS_MANIFEST" = true ]; then
  rm -f "$PLATFORM_DIR/.writ-manifest"
  REMOVED=$((REMOVED + 1))
fi

# Remove rules dir if empty (Cursor)
[ "$PLATFORM" = "cursor" ] && rmdir "$PLATFORM_DIR/rules" 2>/dev/null || true

if [ "$INCLUDE_WRIT" = true ] && [ -d ".writ" ]; then
  rm -rf .writ
  echo "  🗑  Removed .writ/ directory"
fi

echo "  🗑  Removed $REMOVED file(s)"

# ---------------------------------------------------------------------------
# Git commit
# ---------------------------------------------------------------------------

if [ "$NO_COMMIT" = false ] && command -v git &>/dev/null && [ -d .git ]; then
  git add -u "$PLATFORM_DIR/" 2>/dev/null || true
  if [ "$PLATFORM" = "claude" ]; then
    git add -u "CLAUDE.md" 2>/dev/null || true
  fi
  if [ "$INCLUDE_WRIT" = true ]; then
    git add -u ".writ/" 2>/dev/null || true
  fi

  git commit -m "$(cat <<EOF
chore: uninstall Writ ($PLATFORM_LABEL)

Removed commands, agents, rules, and manifest.
$([ "$INCLUDE_WRIT" = true ] && echo "Also removed .writ/ directory." || echo ".writ/ directory preserved.")

See: https://github.com/sellke/writ
EOF
)" 2>/dev/null && echo "  📦 Git commit created." || echo "  ℹ️  Nothing to commit."
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

echo ""
echo "✅ Writ has been removed ($PLATFORM_LABEL)."
echo ""
if [ "$INCLUDE_WRIT" = true ]; then
  echo "  All Writ files including .writ/ have been removed."
else
  echo "  .writ/ directory preserved (specs, docs, ADRs intact)."
  echo "  To also remove: rm -rf .writ"
fi
echo ""
echo "  To reinstall:"
echo "    bash <(curl -s https://raw.githubusercontent.com/sellke/writ/main/scripts/install.sh) --platform $PLATFORM"
echo ""
echo "⚡ So it is written. So it shall be built."

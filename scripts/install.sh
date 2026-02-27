#!/bin/bash
# Writ Installer — sets up writ commands, agents, and rules in your project
# Run from your project root: bash <(curl -s https://raw.githubusercontent.com/sellke/writ/main/scripts/install.sh)
#
# Or clone first:
#   git clone https://github.com/sellke/writ.git /tmp/writ
#   bash /tmp/writ/scripts/install.sh
#
# Flags:
#   --dry-run    Preview changes without applying
#   --no-commit  Don't auto-commit after install

set -euo pipefail

DRY_RUN=false
NO_COMMIT=false
WRIT_SRC=""

for arg in "$@"; do
  case $arg in
    --dry-run)    DRY_RUN=true ;;
    --no-commit)  NO_COMMIT=true ;;
    --help|-h)
      echo "Usage: bash install.sh [--dry-run] [--no-commit]"
      echo ""
      echo "Installs Writ commands, agents, and rules into .cursor/"
      echo "Run from your project root."
      exit 0
      ;;
  esac
done

echo "⚡ Writ Installer"
echo "=================="
echo ""

# Find writ source — either script's directory or clone fresh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WRIT_ROOT="$(dirname "$SCRIPT_DIR")"

if [ -f "$WRIT_ROOT/SKILL.md" ] && [ -d "$WRIT_ROOT/commands" ]; then
  WRIT_SRC="$WRIT_ROOT"
  echo "📦 Using local writ: $WRIT_SRC"
else
  echo "📥 Cloning writ from GitHub..."
  WRIT_SRC=$(mktemp -d)
  git clone --depth 1 https://github.com/sellke/writ.git "$WRIT_SRC" 2>/dev/null
  trap "rm -rf $WRIT_SRC" EXIT
  echo "   Done."
fi

echo ""

# Count what we're installing
CMD_COUNT=$(find "$WRIT_SRC/commands" -name "*.md" | wc -l | tr -d ' ')
AGENT_COUNT=$(find "$WRIT_SRC/agents" -name "*.md" | wc -l | tr -d ' ')

echo "  📋 Commands:  $CMD_COUNT"
echo "  🤖 Agents:    $AGENT_COUNT"
echo "  📜 Rules:     1 (writ.mdc)"
echo "  📖 System:    1 (system-instructions.md)"
echo ""

# --- Overlay-aware copy ---
# Copies files from $1 (source dir) to $2 (local dir), preserving local modifications.
# Returns counts via global variables.
OVERLAY_COPIED=0
OVERLAY_PRESERVED=0
OVERLAY_UNCHANGED=0

overlay_copy() {
  local src_dir="$1"
  local local_dir="$2"
  local label="$3"

  OVERLAY_COPIED=0
  OVERLAY_PRESERVED=0
  OVERLAY_UNCHANGED=0

  for src_file in "$src_dir"/*.md; do
    [ -f "$src_file" ] || continue
    local fname
    fname=$(basename "$src_file")
    local local_file="$local_dir/$fname"

    if [ -f "$local_file" ]; then
      if diff -q "$src_file" "$local_file" > /dev/null 2>&1; then
        OVERLAY_UNCHANGED=$((OVERLAY_UNCHANGED + 1))
      else
        echo "    ⚡ Preserved: $label/$fname (local modifications detected)"
        OVERLAY_PRESERVED=$((OVERLAY_PRESERVED + 1))
      fi
    else
      cp "$src_file" "$local_file"
      OVERLAY_COPIED=$((OVERLAY_COPIED + 1))
    fi
  done
}

overlay_preview() {
  local src_dir="$1"
  local local_dir="$2"
  local label="$3"
  local new=0 preserved=0 unchanged=0

  for src_file in "$src_dir"/*.md; do
    [ -f "$src_file" ] || continue
    local fname
    fname=$(basename "$src_file")
    local local_file="$local_dir/$fname"

    if [ -f "$local_file" ]; then
      if diff -q "$src_file" "$local_file" > /dev/null 2>&1; then
        unchanged=$((unchanged + 1))
      else
        echo "    ⚡ $label/$fname — local modifications (would be preserved)"
        preserved=$((preserved + 1))
      fi
    else
      echo "    ✨ $label/$fname — new (would be copied)"
      new=$((new + 1))
    fi
  done

  [ "$new" -gt 0 ] && echo "    $new new"
  [ "$preserved" -gt 0 ] && echo "    $preserved preserved (local modifications kept)"
  [ "$unchanged" -gt 0 ] && echo "    $unchanged unchanged"
}

if [ "$DRY_RUN" = true ]; then
  echo "🏃 DRY RUN — No changes will be made"
  echo ""
  echo "  Commands:"
  overlay_preview "$WRIT_SRC/commands" ".cursor/commands" "commands"
  echo ""
  echo "  Agents:"
  overlay_preview "$WRIT_SRC/agents" ".cursor/agents" "agents"
  echo ""
  echo "  Rules:   writ.mdc (always updated)"
  echo "  System:  system-instructions.md (always updated)"
  echo ""
  echo "💡 To reset a file to core: delete the local copy and re-run install."
  exit 0
fi

# Install
echo "Installing..."

mkdir -p .cursor/commands .cursor/agents .cursor/rules

echo "  [1/4] Commands..."
overlay_copy "$WRIT_SRC/commands" ".cursor/commands" "commands"
CMD_COPIED=$OVERLAY_COPIED
CMD_PRESERVED=$OVERLAY_PRESERVED

echo "  [2/4] Agents..."
overlay_copy "$WRIT_SRC/agents" ".cursor/agents" "agents"
AGENT_COPIED=$OVERLAY_COPIED
AGENT_PRESERVED=$OVERLAY_PRESERVED

echo "  [3/4] Rules..."
cp "$WRIT_SRC/cursor/writ.mdc" .cursor/rules/

echo "  [4/4] System instructions..."
cp "$WRIT_SRC/system-instructions.md" .cursor/

# Initialize .writ directory if it doesn't exist
if [ ! -d ".writ" ]; then
  echo ""
  echo "  📁 Creating .writ/ directory structure..."
  mkdir -p .writ/{specs,product,research,decision-records,docs,issues,explanations,state}
  
  # Add state to gitignore
  if [ -f .gitignore ] && ! grep -q ".writ/state" .gitignore 2>/dev/null; then
    echo "" >> .gitignore
    echo "# Writ ephemeral state" >> .gitignore
    echo ".writ/state/" >> .gitignore
  fi
fi

# Remove old Code Captain rules if present
if [ -f ".cursor/rules/cc.mdc" ]; then
  echo "  🧹 Removing old Code Captain rules..."
  rm -f .cursor/rules/cc.mdc
fi

echo ""
echo "✅ Writ installed!"

# Overlay summary
TOTAL_PRESERVED=$((CMD_PRESERVED + AGENT_PRESERVED))
if [ "$TOTAL_PRESERVED" -gt 0 ]; then
  echo ""
  echo "  📋 Overlay summary:"
  [ "$CMD_COPIED" -gt 0 ] && echo "     Commands — $CMD_COPIED new"
  [ "$CMD_PRESERVED" -gt 0 ] && echo "     Commands — $CMD_PRESERVED preserved (local modifications kept)"
  [ "$AGENT_COPIED" -gt 0 ] && echo "     Agents   — $AGENT_COPIED new"
  [ "$AGENT_PRESERVED" -gt 0 ] && echo "     Agents   — $AGENT_PRESERVED preserved (local modifications kept)"
  echo ""
  echo "  💡 To reset a file to core: delete the local copy and re-run install."
fi

# Commit
if [ "$NO_COMMIT" = false ]; then
  if command -v git &> /dev/null && [ -d .git ]; then
    git add -A
    git commit -m "chore: install Writ development workflow

Installed $CMD_COUNT commands, $AGENT_COUNT agents, rules, and system instructions.

See: https://github.com/sellke/writ" 2>/dev/null && echo "  📦 Git commit created." || echo "  ℹ️  Nothing to commit (already up to date)."
  fi
fi

echo ""
echo "Usage:"
echo "  In Cursor chat, try: /initialize, /create-spec, /implement-story"
echo ""
echo "⚡ So it is written. So it shall be built."

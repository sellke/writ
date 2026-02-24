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

if [ "$DRY_RUN" = true ]; then
  echo "🏃 DRY RUN — No changes will be made"
  echo ""
  echo "Would install to:"
  echo "  .cursor/commands/*.md"
  echo "  .cursor/agents/*.md"
  echo "  .cursor/rules/writ.mdc"
  echo "  .cursor/system-instructions.md"
  exit 0
fi

# Install
echo "Installing..."

mkdir -p .cursor/commands .cursor/agents .cursor/rules

echo "  [1/4] Commands..."
cp "$WRIT_SRC/commands/"*.md .cursor/commands/

echo "  [2/4] Agents..."
cp "$WRIT_SRC/agents/"*.md .cursor/agents/

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

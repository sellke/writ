#!/bin/bash
# Writ Installer — sets up writ commands, agents, and rules in your project
# Run from your project root: bash <(curl -s https://raw.githubusercontent.com/sellke/writ/main/scripts/install.sh)
#
# Or clone first:
#   git clone https://github.com/sellke/writ.git /tmp/writ
#   bash /tmp/writ/scripts/install.sh
#
# Flags:
#   --dry-run      Preview changes without applying
#   --no-commit    Don't auto-commit after install
#   --force        Overwrite all files, ignoring local modifications
#   --platform     Target platform: cursor (default) or claude

set -euo pipefail

WRIT_REPO="https://github.com/sellke/writ.git"

DRY_RUN=false
NO_COMMIT=false
FORCE=false
PLATFORM="cursor"

while [ $# -gt 0 ]; do
  case $1 in
    --dry-run)    DRY_RUN=true ;;
    --no-commit)  NO_COMMIT=true ;;
    --force)      FORCE=true ;;
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
      echo "Usage: bash install.sh [--dry-run] [--no-commit] [--force] [--platform cursor|claude]"
      echo ""
      echo "Installs Writ commands, agents, and rules into your project."
      echo "Run from your project root."
      echo ""
      echo "Platforms:"
      echo "  cursor (default)  Install into .cursor/ for Cursor IDE"
      echo "  claude            Install into .claude/ for Claude Code CLI"
      echo ""
      echo "Flags:"
      echo "  --dry-run      Preview changes without applying"
      echo "  --no-commit    Don't auto-commit after install"
      echo "  --force        Overwrite existing files/directories"
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
# Platform-specific paths
# ---------------------------------------------------------------------------

if [ "$PLATFORM" = "cursor" ]; then
  PLATFORM_DIR=".cursor"
  MANIFEST_FILE=".cursor/.writ-manifest"
  AGENTS_SRC="agents"
  PLATFORM_LABEL="Cursor"
elif [ "$PLATFORM" = "claude" ]; then
  PLATFORM_DIR=".claude"
  MANIFEST_FILE=".claude/.writ-manifest"
  AGENTS_SRC="claude-code/agents"
  PLATFORM_LABEL="Claude Code"
fi

echo "⚡ Writ Installer ($PLATFORM_LABEL)"
echo "=================="
echo ""

# ---------------------------------------------------------------------------
# Guards
# ---------------------------------------------------------------------------

if [ -f "SKILL.md" ] && [ -d "commands" ] && [ -d "agents" ] && [ -d "scripts" ]; then
  echo "❌ This appears to be the Writ source repository."
  echo "   install.sh is for installing Writ into other projects."
  echo "   This repo uses symlinks — see .writ/docs/self-dogfooding.md"
  exit 1
fi

# ---------------------------------------------------------------------------
# Portable SHA-256
# ---------------------------------------------------------------------------

hash_file() {
  if command -v shasum &>/dev/null; then
    shasum -a 256 "$1" | cut -d' ' -f1
  elif command -v sha256sum &>/dev/null; then
    sha256sum "$1" | cut -d' ' -f1
  else
    openssl dgst -sha256 "$1" | awk '{print $NF}'
  fi
}

# ---------------------------------------------------------------------------
# Manifest helpers
# ---------------------------------------------------------------------------

manifest_version() {
  [ -f "$MANIFEST_FILE" ] && grep '^# version:' "$MANIFEST_FILE" | sed 's/^# version: //' || true
}

manifest_mode() {
  if [ -f "$MANIFEST_FILE" ] && grep -q '^# mode:' "$MANIFEST_FILE"; then
    grep '^# mode:' "$MANIFEST_FILE" | sed 's/^# mode: //'
  else
    echo "copy"
  fi
}

manifest_hash_for() {
  local path="$1"
  [ -f "$MANIFEST_FILE" ] && grep "  ${path}$" "$MANIFEST_FILE" | cut -d' ' -f1 || true
}

write_copy_manifest() {
  local version="$1" target="$2"

  cat > "$target" << EOF
# Writ Manifest — do not edit manually
# Tracks installed file baselines for safe overlay updates.
# mode: copy
# platform: $PLATFORM
# version: $version
# date: $(date -u +%Y-%m-%dT%H:%M:%SZ)
# source: $WRIT_REPO
EOF

  local f rel
  for f in "$PLATFORM_DIR"/commands/*.md "$PLATFORM_DIR"/agents/*.md; do
    [ -f "$f" ] || continue
    rel="${f#"$PLATFORM_DIR"/}"
    echo "$(hash_file "$f")  $rel" >> "$target"
  done

  if [ "$PLATFORM" = "cursor" ]; then
    for f in "$PLATFORM_DIR"/rules/writ.mdc "$PLATFORM_DIR"/system-instructions.md; do
      [ -f "$f" ] || continue
      rel="${f#"$PLATFORM_DIR"/}"
      echo "$(hash_file "$f")  $rel" >> "$target"
    done
  elif [ "$PLATFORM" = "claude" ]; then
    if [ -f "CLAUDE.md" ]; then
      echo "$(hash_file "CLAUDE.md")  CLAUDE.md" >> "$target"
    fi
  fi
}

# ---------------------------------------------------------------------------
# Resolve writ source
# ---------------------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WRIT_ROOT="$(dirname "$SCRIPT_DIR")"
WRIT_SRC=""

if [ -f "$WRIT_ROOT/SKILL.md" ] && [ -d "$WRIT_ROOT/commands" ]; then
  WRIT_SRC="$WRIT_ROOT"
  echo "📦 Using local writ: $WRIT_SRC"
else
  if ! command -v git &>/dev/null; then
    echo "❌ git is required to clone Writ. Install git or clone manually first."
    exit 1
  fi
  echo "📥 Cloning writ from GitHub..."
  WRIT_SRC=$(mktemp -d)
  if ! git clone --depth 1 "$WRIT_REPO" "$WRIT_SRC" 2>&1 | tail -1; then
    echo "❌ Failed to clone $WRIT_REPO"
    echo "   Check your network connection and try again."
    rm -rf "$WRIT_SRC"
    exit 1
  fi
  cleanup() { rm -rf "$WRIT_SRC"; }
  trap cleanup EXIT
  echo "   Done."
fi

VERSION=$(cd "$WRIT_SRC" && git log -1 --format="%h" 2>/dev/null || echo "unknown")
VERSION_LONG=$(cd "$WRIT_SRC" && git log -1 --format="%h %s" 2>/dev/null || echo "unknown")

echo ""

# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------

CMD_COUNT=0
for f in "$WRIT_SRC/commands"/*.md; do [ -f "$f" ] && CMD_COUNT=$((CMD_COUNT + 1)); done
AGENT_COUNT=0
for f in "$WRIT_SRC/$AGENTS_SRC"/*.md; do [ -f "$f" ] && AGENT_COUNT=$((AGENT_COUNT + 1)); done

echo "  📋 Commands:  $CMD_COUNT"
echo "  🤖 Agents:    $AGENT_COUNT"
if [ "$PLATFORM" = "cursor" ]; then
  echo "  📜 Rules:     1 (writ.mdc)"
  echo "  📖 System:    1 (system-instructions.md)"
elif [ "$PLATFORM" = "claude" ]; then
  echo "  📖 Root:      1 (CLAUDE.md)"
fi
echo "  🎯 Platform:  $PLATFORM_LABEL"
echo "  📌 Version:   $VERSION_LONG"
echo ""

EXISTING_VERSION=$(manifest_version)
EXISTING_MODE=$(manifest_mode)

if [ -n "$EXISTING_VERSION" ]; then
  echo "  ℹ️  Existing installation (version: $EXISTING_VERSION, mode: $EXISTING_MODE)"
  if [ "$EXISTING_MODE" = "link" ]; then
    echo "  ⚠️  Converting linked → copied installation"
  fi
  echo ""
fi

# ---------------------------------------------------------------------------
# Shared: .writ/ workspace + legacy cleanup
# ---------------------------------------------------------------------------

init_writ_workspace() {
  if [ ! -d ".writ" ]; then
    echo ""
    echo "  📁 Creating .writ/ directory structure..."
    mkdir -p .writ/{specs,product,research,decision-records,docs,issues,explanations,state}

    if [ -f .gitignore ] && ! grep -q ".writ/state" .gitignore 2>/dev/null; then
      printf '\n# Writ ephemeral state\n.writ/state/\n' >> .gitignore
    fi
  fi

  if [ -f ".cursor/rules/cc.mdc" ]; then
    echo "  🧹 Removing old Code Captain rules..."
    rm -f .cursor/rules/cc.mdc
  fi
}

# ===========================================================================
# COPY MODE
# ===========================================================================

# ---------------------------------------------------------------------------
# Three-way overlay logic
# ---------------------------------------------------------------------------

_NEW=0; _UPDATED=0; _PRESERVED=0; _UNCHANGED=0

overlay_scan() {
  local src_dir="$1" local_dir="$2" label="$3" mode="$4"
  _NEW=0; _UPDATED=0; _PRESERVED=0; _UNCHANGED=0

  local src_file fname local_file rel_path upstream_hash local_hash baseline_hash
  for src_file in "$src_dir"/*.md; do
    [ -f "$src_file" ] || continue
    fname=$(basename "$src_file")
    local_file="$local_dir/$fname"
    rel_path="${label}/${fname}"
    upstream_hash=$(hash_file "$src_file")

    if [ ! -f "$local_file" ]; then
      _NEW=$((_NEW + 1))
      if [ "$mode" = "preview" ]; then echo "    ✨ New:       $rel_path"; fi
      if [ "$mode" = "apply" ];   then cp "$src_file" "$local_file"; fi
      continue
    fi

    local_hash=$(hash_file "$local_file")

    if [ "$local_hash" = "$upstream_hash" ]; then
      _UNCHANGED=$((_UNCHANGED + 1))
      continue
    fi

    baseline_hash=$(manifest_hash_for "$rel_path")

    if [ "$FORCE" = true ]; then
      _UPDATED=$((_UPDATED + 1))
      if [ "$mode" = "preview" ]; then echo "    🔄 Update:    $rel_path (forced)"; fi
      if [ "$mode" = "apply" ];   then cp "$src_file" "$local_file"; fi
    elif [ -z "$baseline_hash" ]; then
      _PRESERVED=$((_PRESERVED + 1))
      if [ "$mode" = "preview" ]; then echo "    ⚡ Preserved: $rel_path (no baseline, assuming modified)"; fi
    elif [ "$local_hash" = "$baseline_hash" ]; then
      _UPDATED=$((_UPDATED + 1))
      if [ "$mode" = "preview" ]; then echo "    🔄 Update:    $rel_path"; fi
      if [ "$mode" = "apply" ];   then cp "$src_file" "$local_file"; fi
    else
      _PRESERVED=$((_PRESERVED + 1))
      if [ "$mode" = "preview" ]; then echo "    ⚡ Preserved: $rel_path (local modifications)"; fi
    fi
  done
}

# --- Dry run ---

if [ "$DRY_RUN" = true ]; then
  echo "🏃 DRY RUN — No changes will be made"
  echo ""
  if [ "$EXISTING_MODE" = "link" ]; then
    echo "  Would replace symlinks with copies ($CMD_COUNT commands, $AGENT_COUNT agents)."
  else
    echo "  Commands:"
    overlay_scan "$WRIT_SRC/commands" "$PLATFORM_DIR/commands" "commands" "preview"
    echo ""
    echo "  Agents:"
    overlay_scan "$WRIT_SRC/$AGENTS_SRC" "$PLATFORM_DIR/agents" "agents" "preview"
    echo ""
    if [ "$PLATFORM" = "cursor" ]; then
      echo "  Rules:   writ.mdc → always updated"
      echo "  System:  system-instructions.md → always updated"
    elif [ "$PLATFORM" = "claude" ]; then
      echo "  Root:    CLAUDE.md → always updated"
    fi
  fi
  echo ""
  echo "💡 To reset a file to core: delete the local copy and re-run install."
  echo "💡 To force overwrite all: install.sh --force"
  exit 0
fi

# --- Install ---

echo "Installing..."

# Remove symlinks if converting from a linked installation
if [ "$EXISTING_MODE" = "link" ]; then
  echo "  Removing symlinks..."
  for f in "$PLATFORM_DIR"/commands/*.md "$PLATFORM_DIR"/agents/*.md; do
    [ -L "$f" ] && rm -f "$f"
  done
  for f in "$PLATFORM_DIR/commands" "$PLATFORM_DIR/agents"; do
    [ -L "$f" ] && rm -f "$f"
  done
  if [ "$PLATFORM" = "cursor" ]; then
    for f in "$PLATFORM_DIR/rules/writ.mdc" "$PLATFORM_DIR/system-instructions.md"; do
      [ -L "$f" ] && rm -f "$f"
    done
  elif [ "$PLATFORM" = "claude" ]; then
    [ -L "CLAUDE.md" ] && rm -f "CLAUDE.md"
  fi
fi

mkdir -p "$PLATFORM_DIR/commands" "$PLATFORM_DIR/agents"
[ "$PLATFORM" = "cursor" ] && mkdir -p "$PLATFORM_DIR/rules"

STEP_TOTAL=5
STEP=0

STEP=$((STEP + 1))
echo "  [$STEP/$STEP_TOTAL] Commands..."
overlay_scan "$WRIT_SRC/commands" "$PLATFORM_DIR/commands" "commands" "apply"
CMD_NEW=$_NEW; CMD_UPDATED=$_UPDATED; CMD_PRESERVED=$_PRESERVED

STEP=$((STEP + 1))
echo "  [$STEP/$STEP_TOTAL] Agents..."
overlay_scan "$WRIT_SRC/$AGENTS_SRC" "$PLATFORM_DIR/agents" "agents" "apply"
AGENT_NEW=$_NEW; AGENT_UPDATED=$_UPDATED; AGENT_PRESERVED=$_PRESERVED

STEP=$((STEP + 1))
if [ "$PLATFORM" = "cursor" ]; then
  echo "  [$STEP/$STEP_TOTAL] Rules..."
  cp "$WRIT_SRC/cursor/writ.mdc" "$PLATFORM_DIR/rules/"

  STEP=$((STEP + 1))
  echo "  [$STEP/$STEP_TOTAL] System instructions..."
  cp "$WRIT_SRC/system-instructions.md" "$PLATFORM_DIR/"
elif [ "$PLATFORM" = "claude" ]; then
  echo "  [$STEP/$STEP_TOTAL] CLAUDE.md..."
  cp "$WRIT_SRC/claude-code/CLAUDE.md" "CLAUDE.md"
  STEP=$((STEP + 1))
  echo "  [$STEP/$STEP_TOTAL] (skipped — no system-instructions for Claude Code)"
fi

STEP=$((STEP + 1))
echo "  [$STEP/$STEP_TOTAL] Writing manifest..."
write_copy_manifest "$VERSION" "$MANIFEST_FILE"

init_writ_workspace

# --- Summary ---

echo ""
echo "✅ Writ installed for $PLATFORM_LABEL! (version: $VERSION)"

TOTAL_NEW=$((CMD_NEW + AGENT_NEW))
TOTAL_UPDATED=$((CMD_UPDATED + AGENT_UPDATED))
TOTAL_PRESERVED=$((CMD_PRESERVED + AGENT_PRESERVED))

if [ "$TOTAL_NEW" -gt 0 ] || [ "$TOTAL_UPDATED" -gt 0 ] || [ "$TOTAL_PRESERVED" -gt 0 ]; then
  echo ""
  echo "  📋 Summary:"
  [ "$TOTAL_NEW" -gt 0 ]       && echo "     $TOTAL_NEW new file(s) installed"
  [ "$TOTAL_UPDATED" -gt 0 ]   && echo "     $TOTAL_UPDATED file(s) updated"
  [ "$TOTAL_PRESERVED" -gt 0 ] && echo "     $TOTAL_PRESERVED file(s) preserved (local modifications kept)"
  if [ "$TOTAL_PRESERVED" -gt 0 ]; then
    echo ""
    echo "  💡 To reset a file to core: delete it and re-run install."
    echo "  💡 To force overwrite all: install.sh --force"
  fi
fi

# --- Scoped git commit ---

if [ "$NO_COMMIT" = false ] && command -v git &>/dev/null && [ -d .git ]; then
  git add "$PLATFORM_DIR/commands/" "$PLATFORM_DIR/agents/" 2>/dev/null || true
  if [ "$PLATFORM" = "cursor" ]; then
    git add "$PLATFORM_DIR/rules/writ.mdc" "$PLATFORM_DIR/system-instructions.md" 2>/dev/null || true
  elif [ "$PLATFORM" = "claude" ]; then
    git add "CLAUDE.md" 2>/dev/null || true
  fi
  git add "$MANIFEST_FILE" 2>/dev/null || true
  [ -d .writ ] && git add .writ/ 2>/dev/null || true
  [ -f .gitignore ] && git add .gitignore 2>/dev/null || true

  git commit -m "$(cat <<EOF
chore: install Writ development workflow ($PLATFORM_LABEL)

See: https://github.com/sellke/writ
EOF
)" 2>/dev/null && echo "  📦 Git commit created." || echo "  ℹ️  Nothing to commit (already up to date)."
fi

echo ""
echo "Usage:"
if [ "$PLATFORM" = "cursor" ]; then
  echo "  In Cursor chat, try: /initialize, /create-spec, /implement-story"
elif [ "$PLATFORM" = "claude" ]; then
  echo "  In Claude Code, try: /create-spec, /implement-story, /status"
fi
echo ""
echo "⚡ So it is written. So it shall be built."

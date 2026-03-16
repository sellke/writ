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
#   --link [path]  Symlink to a writ checkout instead of copying

set -euo pipefail

WRIT_REPO="https://github.com/sellke/writ.git"
WRIT_GLOBAL="$HOME/.writ"
MANIFEST_FILE=".cursor/.writ-manifest"

DRY_RUN=false
NO_COMMIT=false
FORCE=false
LINK_MODE=false
LINK_PATH=""

while [ $# -gt 0 ]; do
  case $1 in
    --dry-run)    DRY_RUN=true ;;
    --no-commit)  NO_COMMIT=true ;;
    --force)      FORCE=true ;;
    --link)
      LINK_MODE=true
      if [ $# -gt 1 ] && [[ ! "$2" =~ ^-- ]]; then
        LINK_PATH="$2"
        shift
      fi
      ;;
    --help|-h)
      echo "Usage: bash install.sh [--dry-run] [--no-commit] [--force] [--link [path]]"
      echo ""
      echo "Installs Writ commands, agents, and rules into .cursor/"
      echo "Run from your project root."
      echo ""
      echo "Modes:"
      echo "  (default)      Copy files into .cursor/ — self-contained, git-portable,"
      echo "                 supports per-project customization via overlay."
      echo "  --link [path]  Symlink .cursor/ to a writ checkout — always in sync,"
      echo "                 update with 'git pull'. Not committed to git."
      echo "                 Without a path, uses ~/.writ (auto-cloned if needed)."
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

echo "⚡ Writ Installer"
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
# version: $version
# date: $(date -u +%Y-%m-%dT%H:%M:%SZ)
# source: $WRIT_REPO
EOF

  local f rel
  for f in .cursor/commands/*.md .cursor/agents/*.md; do
    [ -f "$f" ] || continue
    rel="${f#.cursor/}"
    echo "$(hash_file "$f")  $rel" >> "$target"
  done
  for f in .cursor/rules/writ.mdc .cursor/system-instructions.md; do
    [ -f "$f" ] || continue
    rel="${f#.cursor/}"
    echo "$(hash_file "$f")  $rel" >> "$target"
  done
}

write_link_manifest() {
  local version="$1" target="$2" link_target="$3"

  cat > "$target" << EOF
# Writ Manifest — do not edit manually
# mode: link
# link_target: $link_target
# version: $version
# date: $(date -u +%Y-%m-%dT%H:%M:%SZ)
# source: $WRIT_REPO
EOF
}

# ---------------------------------------------------------------------------
# Resolve writ source
# ---------------------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WRIT_ROOT="$(dirname "$SCRIPT_DIR")"
WRIT_SRC=""

if [ "$LINK_MODE" = true ] && [ -n "$LINK_PATH" ]; then
  # Explicit --link /path
  if [ ! -d "$LINK_PATH" ]; then
    echo "❌ Path not found: $LINK_PATH"
    exit 1
  fi
  WRIT_SRC="$(cd "$LINK_PATH" && pwd)"
  if [ ! -f "$WRIT_SRC/SKILL.md" ] || [ ! -d "$WRIT_SRC/commands" ]; then
    echo "❌ $WRIT_SRC doesn't look like a writ checkout."
    exit 1
  fi
  echo "🔗 Link target: $WRIT_SRC"

elif [ -f "$WRIT_ROOT/SKILL.md" ] && [ -d "$WRIT_ROOT/commands" ]; then
  # Running from a local writ checkout (e.g. /tmp/writ/scripts/install.sh)
  WRIT_SRC="$WRIT_ROOT"
  if [ "$LINK_MODE" = true ]; then
    echo "🔗 Link target: $WRIT_SRC"
  else
    echo "📦 Using local writ: $WRIT_SRC"
  fi

elif [ "$LINK_MODE" = true ]; then
  # --link with no path and no local checkout → use ~/.writ
  WRIT_SRC="$WRIT_GLOBAL"
  if [ ! -d "$WRIT_SRC" ]; then
    if ! command -v git &>/dev/null; then
      echo "❌ git is required to clone Writ. Install git or pass --link /path."
      exit 1
    fi
    echo "📥 Cloning writ to $WRIT_SRC..."
    if ! git clone "$WRIT_REPO" "$WRIT_SRC" 2>&1 | tail -1; then
      echo "❌ Failed to clone $WRIT_REPO"
      rm -rf "$WRIT_SRC"
      exit 1
    fi
    echo "   Done."
  fi
  if [ ! -f "$WRIT_SRC/SKILL.md" ] || [ ! -d "$WRIT_SRC/commands" ]; then
    echo "❌ $WRIT_SRC doesn't look like a writ checkout."
    exit 1
  fi
  echo "🔗 Link target: $WRIT_SRC"

else
  # Copy mode — clone to temp dir
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
for f in "$WRIT_SRC/agents"/*.md; do [ -f "$f" ] && AGENT_COUNT=$((AGENT_COUNT + 1)); done

echo "  📋 Commands:  $CMD_COUNT"
echo "  🤖 Agents:    $AGENT_COUNT"
echo "  📜 Rules:     1 (writ.mdc)"
echo "  📖 System:    1 (system-instructions.md)"
echo "  📌 Version:   $VERSION_LONG"
if [ "$LINK_MODE" = true ]; then
  echo "  🔗 Mode:      linked → $WRIT_SRC"
fi
echo ""

EXISTING_VERSION=$(manifest_version)
EXISTING_MODE=$(manifest_mode)

if [ -n "$EXISTING_VERSION" ]; then
  echo "  ℹ️  Existing installation (version: $EXISTING_VERSION, mode: $EXISTING_MODE)"
  if [ "$EXISTING_MODE" = "link" ] && [ "$LINK_MODE" = false ]; then
    echo "  ⚠️  Switching from linked → copied installation"
  elif [ "$EXISTING_MODE" != "link" ] && [ "$LINK_MODE" = true ]; then
    echo "  ⚠️  Switching from copied → linked installation"
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
# LINK MODE
# ===========================================================================

if [ "$LINK_MODE" = true ]; then

  # --- Dry run (link) ---
  if [ "$DRY_RUN" = true ]; then
    echo "🏃 DRY RUN — No changes will be made"
    echo ""
    echo "  Would create per-file symlinks:"
    for f in "$WRIT_SRC/commands"/*.md; do
      [ -f "$f" ] && echo "    .cursor/commands/$(basename "$f") → $f"
    done
    for f in "$WRIT_SRC/agents"/*.md; do
      [ -f "$f" ] && echo "    .cursor/agents/$(basename "$f")   → $f"
    done
    echo "    .cursor/rules/writ.mdc         → $WRIT_SRC/cursor/writ.mdc"
    echo "    .cursor/system-instructions.md → $WRIT_SRC/system-instructions.md"
    echo ""
    echo "  ℹ️  Update writ with: cd $WRIT_SRC && git pull"
    echo "     Then re-run install to pick up new files."
    exit 0
  fi

  # --- Install (link) ---
  echo "Installing (linked)..."
  mkdir -p .cursor/commands .cursor/agents .cursor/rules

  # If commands/ or agents/ is currently a directory symlink (old-style link
  # install), remove it so we can recreate as a real directory with file symlinks.
  for dir in commands agents; do
    if [ -L ".cursor/$dir" ]; then
      echo "  ⚠️  Replacing .cursor/$dir/ directory symlink with per-file symlinks"
      rm -f ".cursor/$dir"
      mkdir -p ".cursor/$dir"
    fi
  done

  echo "  [1/4] Linking commands..."
  LINK_CMD=0
  for f in "$WRIT_SRC/commands"/*.md; do
    [ -f "$f" ] || continue
    fname=$(basename "$f")
    ln -sf "$f" ".cursor/commands/$fname"
    LINK_CMD=$((LINK_CMD + 1))
  done
  echo "         $LINK_CMD command(s) → $WRIT_SRC/commands/"

  # Remove stale command symlinks that no longer exist in source
  for f in .cursor/commands/*.md; do
    [ -L "$f" ] || continue
    fname=$(basename "$f")
    [ -f "$WRIT_SRC/commands/$fname" ] || rm -f "$f"
  done

  echo "  [2/4] Linking agents..."
  LINK_AGENT=0
  for f in "$WRIT_SRC/agents"/*.md; do
    [ -f "$f" ] || continue
    fname=$(basename "$f")
    ln -sf "$f" ".cursor/agents/$fname"
    LINK_AGENT=$((LINK_AGENT + 1))
  done
  echo "         $LINK_AGENT agent(s)  → $WRIT_SRC/agents/"

  for f in .cursor/agents/*.md; do
    [ -L "$f" ] || continue
    fname=$(basename "$f")
    [ -f "$WRIT_SRC/agents/$fname" ] || rm -f "$f"
  done

  echo "  [3/4] Linking rules and system instructions..."
  ln -sf "$WRIT_SRC/cursor/writ.mdc" .cursor/rules/writ.mdc
  ln -sf "$WRIT_SRC/system-instructions.md" .cursor/system-instructions.md

  echo "  [4/4] Writing manifest..."
  write_link_manifest "$VERSION" "$MANIFEST_FILE" "$WRIT_SRC"

  init_writ_workspace

  echo ""
  echo "✅ Writ installed! (version: $VERSION, linked to $WRIT_SRC)"
  echo ""
  echo "  ℹ️  Update writ: cd $WRIT_SRC && git pull"
  echo "     Then re-run install to pick up new files."

  if [ "$NO_COMMIT" = false ] && command -v git &>/dev/null && [ -d .git ]; then
    git add "$MANIFEST_FILE" 2>/dev/null || true
    git add .cursor/commands/ .cursor/agents/ .cursor/rules/writ.mdc \
            .cursor/system-instructions.md 2>/dev/null || true
    [ -d .writ ] && git add .writ/ 2>/dev/null || true
    [ -f .gitignore ] && git add .gitignore 2>/dev/null || true

    git commit -m "$(cat <<'EOF'
chore: install Writ development workflow (linked)

See: https://github.com/sellke/writ
EOF
)" 2>/dev/null && echo "  📦 Git commit created." || echo "  ℹ️  Nothing to commit (already up to date)."
  fi

  echo ""
  echo "Usage:"
  echo "  In Cursor chat, try: /initialize, /create-spec, /implement-story"
  echo ""
  echo "⚡ So it is written. So it shall be built."
  exit 0
fi

# ===========================================================================
# COPY MODE
# ===========================================================================

# ---------------------------------------------------------------------------
# Three-way overlay logic
#
# For each source file, determine action by comparing three states:
#   upstream  — the new file from writ source
#   baseline  — the hash recorded in the manifest at last install/update
#   local     — the file currently on disk
#
# Decision matrix:
#   No local file             → install (new)
#   local == upstream         → skip (already current)
#   local == baseline         → update (user hasn't touched it)
#   local != baseline         → preserve (user modified) unless --force
#   No baseline (old install) → preserve if differs (conservative)
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
      [ "$mode" = "preview" ] && echo "    ✨ New:       $rel_path"
      [ "$mode" = "apply" ]   && cp "$src_file" "$local_file"
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
      [ "$mode" = "preview" ] && echo "    🔄 Update:    $rel_path (forced)"
      [ "$mode" = "apply" ]   && cp "$src_file" "$local_file"
    elif [ -z "$baseline_hash" ]; then
      _PRESERVED=$((_PRESERVED + 1))
      [ "$mode" = "preview" ] && echo "    ⚡ Preserved: $rel_path (no baseline, assuming modified)"
    elif [ "$local_hash" = "$baseline_hash" ]; then
      _UPDATED=$((_UPDATED + 1))
      [ "$mode" = "preview" ] && echo "    🔄 Update:    $rel_path"
      [ "$mode" = "apply" ]   && cp "$src_file" "$local_file"
    else
      _PRESERVED=$((_PRESERVED + 1))
      [ "$mode" = "preview" ] && echo "    ⚡ Preserved: $rel_path (local modifications)"
    fi
  done
}

# --- Dry run (copy) ---

if [ "$DRY_RUN" = true ]; then
  echo "🏃 DRY RUN — No changes will be made"
  echo ""
  if [ "$EXISTING_MODE" = "link" ]; then
    echo "  Would replace symlinks with copies ($CMD_COUNT commands, $AGENT_COUNT agents,"
    echo "  rules, and system instructions)."
  else
    echo "  Commands:"
    overlay_scan "$WRIT_SRC/commands" ".cursor/commands" "commands" "preview"
    echo ""
    echo "  Agents:"
    overlay_scan "$WRIT_SRC/agents" ".cursor/agents" "agents" "preview"
    echo ""
    echo "  Rules:   writ.mdc → always updated"
    echo "  System:  system-instructions.md → always updated"
  fi
  echo ""
  echo "💡 To reset a file to core: delete the local copy and re-run install."
  echo "💡 To force overwrite all: install.sh --force"
  echo "💡 To symlink instead:     install.sh --link"
  exit 0
fi

# --- Install (copy) ---

echo "Installing..."

# Remove symlinks if switching from link to copy mode
if [ "$EXISTING_MODE" = "link" ]; then
  echo "  Removing symlinks..."
  for item in .cursor/commands .cursor/agents .cursor/rules/writ.mdc .cursor/system-instructions.md; do
    [ -L "$item" ] && rm -f "$item"
  done
fi

mkdir -p .cursor/commands .cursor/agents .cursor/rules

echo "  [1/5] Commands..."
overlay_scan "$WRIT_SRC/commands" ".cursor/commands" "commands" "apply"
CMD_NEW=$_NEW; CMD_UPDATED=$_UPDATED; CMD_PRESERVED=$_PRESERVED

echo "  [2/5] Agents..."
overlay_scan "$WRIT_SRC/agents" ".cursor/agents" "agents" "apply"
AGENT_NEW=$_NEW; AGENT_UPDATED=$_UPDATED; AGENT_PRESERVED=$_PRESERVED

echo "  [3/5] Rules..."
cp "$WRIT_SRC/cursor/writ.mdc" .cursor/rules/

echo "  [4/5] System instructions..."
cp "$WRIT_SRC/system-instructions.md" .cursor/

echo "  [5/5] Writing manifest..."
write_copy_manifest "$VERSION" "$MANIFEST_FILE"

init_writ_workspace

# --- Summary (copy) ---

echo ""
echo "✅ Writ installed! (version: $VERSION)"

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

# --- Scoped git commit (copy) ---

if [ "$NO_COMMIT" = false ] && command -v git &>/dev/null && [ -d .git ]; then
  git add \
    .cursor/commands/ .cursor/agents/ .cursor/rules/writ.mdc \
    .cursor/system-instructions.md "$MANIFEST_FILE" 2>/dev/null || true
  [ -d .writ ] && git add .writ/ 2>/dev/null || true
  [ -f .gitignore ] && git add .gitignore 2>/dev/null || true

  git commit -m "$(cat <<'EOF'
chore: install Writ development workflow

See: https://github.com/sellke/writ
EOF
)" 2>/dev/null && echo "  📦 Git commit created." || echo "  ℹ️  Nothing to commit (already up to date)."
fi

echo ""
echo "Usage:"
echo "  In Cursor chat, try: /initialize, /create-spec, /implement-story"
echo ""
echo "⚡ So it is written. So it shall be built."

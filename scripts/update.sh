#!/bin/bash
# Writ Updater — pulls latest writ and syncs installed files
# Run from your project root: bash <(curl -s https://raw.githubusercontent.com/sellke/writ/main/scripts/update.sh)
#
# Uses the manifest to distinguish upstream changes from local modifications.
# Files you've customized are never overwritten.
#
# Flags:
#   --dry-run    Preview changes without applying
#   --no-commit  Don't auto-commit after update
#   --force      Overwrite all files, ignoring local modifications
#   --platform   Target platform: cursor (default) or claude

set -euo pipefail

WRIT_REPO="https://github.com/sellke/writ.git"

DRY_RUN=false
NO_COMMIT=false
FORCE=false
PLATFORM="cursor"

for arg in "$@"; do
  case $arg in
    --dry-run)    DRY_RUN=true ;;
    --no-commit)  NO_COMMIT=true ;;
    --force)      FORCE=true ;;
    --platform)   ;; # value handled below
    --help|-h)
      echo "Usage: bash update.sh [--dry-run] [--no-commit] [--force] [--platform cursor|claude]"
      echo ""
      echo "Updates Writ commands, agents, and rules from latest GitHub release."
      echo "Run from your project root."
      echo ""
      echo "Platforms:"
      echo "  cursor (default)  Update .cursor/ installation"
      echo "  claude            Update .claude/ installation"
      echo ""
      echo "Flags:"
      echo "  --dry-run    Preview changes without applying"
      echo "  --no-commit  Don't auto-commit after update"
      echo "  --force      Overwrite all files, ignoring local modifications"
      exit 0
      ;;
  esac
done

# Parse --platform value (needs two-pass since for-loop can't easily handle --flag value)
ARGS=("$@")
for i in "${!ARGS[@]}"; do
  if [ "${ARGS[$i]}" = "--platform" ]; then
    PLATFORM="${ARGS[$((i+1))]:-}"
    if [ "$PLATFORM" != "cursor" ] && [ "$PLATFORM" != "claude" ]; then
      echo "❌ Unknown platform: $PLATFORM"
      echo "   Supported: cursor, claude"
      exit 1
    fi
    break
  fi
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

echo "⚡ Writ Updater ($PLATFORM_LABEL)"
echo "================"
echo ""

# ---------------------------------------------------------------------------
# Guards
# ---------------------------------------------------------------------------

if [ "$PLATFORM" = "cursor" ]; then
  if [ ! -d "$PLATFORM_DIR/commands" ] || [ ! -f "$PLATFORM_DIR/rules/writ.mdc" ]; then
    echo "❌ Writ doesn't appear to be installed for $PLATFORM_LABEL in this project."
    echo "   Run install.sh --platform $PLATFORM first."
    exit 1
  fi
elif [ "$PLATFORM" = "claude" ]; then
  if [ ! -d "$PLATFORM_DIR/commands" ] || [ ! -f "CLAUDE.md" ]; then
    echo "❌ Writ doesn't appear to be installed for $PLATFORM_LABEL in this project."
    echo "   Run install.sh --platform $PLATFORM first."
    exit 1
  fi
fi

if [ -f "SKILL.md" ] && [ -d "commands" ] && [ -d "agents" ] && [ -d "scripts" ]; then
  echo "❌ This appears to be the Writ source repository."
  echo "   update.sh is for updating Writ in other projects."
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

manifest_files() {
  [ -f "$MANIFEST_FILE" ] && grep -v '^#' "$MANIFEST_FILE" | grep -v '^$' | awk '{print $2}' || true
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
# Linked installation guard — must convert first
# ---------------------------------------------------------------------------

if [ "$(manifest_mode)" = "link" ]; then
  echo "❌ This is a linked Writ installation."
  echo "   Linked installations cannot be updated with update.sh."
  echo ""
  echo "   To convert to a copy-based installation:"
  echo "     bash <(curl -s https://raw.githubusercontent.com/sellke/writ/main/scripts/unlink.sh)"
  echo ""
  echo "   Then re-run update.sh."
  exit 1
fi

# ===========================================================================
# COPY MODE
# ===========================================================================

# ---------------------------------------------------------------------------
# Clone latest
# ---------------------------------------------------------------------------

if ! command -v git &>/dev/null; then
  echo "❌ git is required. Install git and try again."
  exit 1
fi

echo "📥 Fetching latest writ..."
WRIT_SRC=$(mktemp -d)
if ! git clone --depth 1 "$WRIT_REPO" "$WRIT_SRC" 2>&1 | tail -1; then
  echo "❌ Failed to clone $WRIT_REPO"
  echo "   Check your network connection and try again."
  rm -rf "$WRIT_SRC"
  exit 1
fi
cleanup() { rm -rf "$WRIT_SRC"; }
trap cleanup EXIT

NEW_VERSION=$(cd "$WRIT_SRC" && git log -1 --format="%h" 2>/dev/null || echo "unknown")
NEW_VERSION_LONG=$(cd "$WRIT_SRC" && git log -1 --format="%h %s" 2>/dev/null || echo "unknown")
CURRENT_VERSION=$(manifest_version)

echo "   Installed: ${CURRENT_VERSION:-unknown (no manifest)}"
echo "   Latest:    $NEW_VERSION_LONG"
echo ""

if [ -z "$CURRENT_VERSION" ]; then
  echo "  ⚠️  No manifest found — this is an older installation."
  echo "     Files that differ from upstream will be treated conservatively"
  echo "     (assumed locally modified). A manifest will be created after update."
  echo ""
fi

# ---------------------------------------------------------------------------
# Three-way scan
# ---------------------------------------------------------------------------

_NEW=0; _UPDATED=0; _PRESERVED=0; _UNCHANGED=0
_PRESERVED_FILES=""

overlay_scan() {
  local src_dir="$1" local_dir="$2" label="$3" mode="$4"
  _NEW=0; _UPDATED=0; _PRESERVED=0; _UNCHANGED=0
  _PRESERVED_FILES=""

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
      _PRESERVED_FILES="${_PRESERVED_FILES}    ${rel_path}\n"
      if [ "$mode" = "preview" ]; then echo "    ⚡ Preserved: $rel_path (no baseline, assuming modified)"; fi
    elif [ "$local_hash" = "$baseline_hash" ]; then
      _UPDATED=$((_UPDATED + 1))
      if [ "$mode" = "preview" ]; then echo "    🔄 Update:    $rel_path"; fi
      if [ "$mode" = "apply" ];   then cp "$src_file" "$local_file"; fi
    else
      _PRESERVED=$((_PRESERVED + 1))
      _PRESERVED_FILES="${_PRESERVED_FILES}    ${rel_path}\n"
      if [ "$mode" = "preview" ]; then echo "    ⚡ Preserved: $rel_path (local modifications)"; fi
    fi
  done
}

# ---------------------------------------------------------------------------
# Stale file detection — files in manifest but removed upstream
# ---------------------------------------------------------------------------

STALE_FILES=""
STALE_COUNT=0

detect_stale_files() {
  local manifest_path local_file upstream_file baseline_hash local_hash category
  while IFS= read -r manifest_path; do
    [ -z "$manifest_path" ] && continue

    # CLAUDE.md lives at project root, not inside the platform dir
    if [ "$manifest_path" = "CLAUDE.md" ]; then
      local_file="CLAUDE.md"
    else
      local_file="$PLATFORM_DIR/$manifest_path"
    fi
    [ -f "$local_file" ] || continue

    category="${manifest_path%%/*}"
    case "$category" in
      commands) upstream_file="$WRIT_SRC/commands/$(basename "$manifest_path")" ;;
      agents)   upstream_file="$WRIT_SRC/$AGENTS_SRC/$(basename "$manifest_path")" ;;
      rules)    upstream_file="$WRIT_SRC/cursor/$(basename "$manifest_path")" ;;
      CLAUDE.md) upstream_file="$WRIT_SRC/claude-code/CLAUDE.md" ;;
      *)        continue ;;
    esac

    if [ ! -f "$upstream_file" ]; then
      baseline_hash=$(manifest_hash_for "$manifest_path")
      local_hash=$(hash_file "$local_file")

      if [ "$local_hash" = "$baseline_hash" ]; then
        STALE_FILES="${STALE_FILES}${manifest_path}\n"
        STALE_COUNT=$((STALE_COUNT + 1))
      fi
    fi
  done <<< "$(manifest_files)"
}

# ---------------------------------------------------------------------------
# Phase 1: Scan
# ---------------------------------------------------------------------------

echo "Scanning for changes..."
echo ""

echo "  Commands:"
overlay_scan "$WRIT_SRC/commands" "$PLATFORM_DIR/commands" "commands" "preview"
TOTAL_NEW=$_NEW; TOTAL_UPDATED=$_UPDATED; TOTAL_PRESERVED=$_PRESERVED
ALL_PRESERVED_FILES="$_PRESERVED_FILES"
CMD_UNCHANGED=$_UNCHANGED

echo "  Agents:"
overlay_scan "$WRIT_SRC/$AGENTS_SRC" "$PLATFORM_DIR/agents" "agents" "preview"
TOTAL_NEW=$((TOTAL_NEW + _NEW))
TOTAL_UPDATED=$((TOTAL_UPDATED + _UPDATED))
TOTAL_PRESERVED=$((TOTAL_PRESERVED + _PRESERVED))
ALL_PRESERVED_FILES="${ALL_PRESERVED_FILES}${_PRESERVED_FILES}"
AGENT_UNCHANGED=$_UNCHANGED

# Platform-specific special files with three-way logic
if [ "$PLATFORM" = "cursor" ]; then
  RULE_ACTION="unchanged"
  if [ -f "$PLATFORM_DIR/rules/writ.mdc" ]; then
    rule_upstream=$(hash_file "$WRIT_SRC/cursor/writ.mdc")
    rule_local=$(hash_file "$PLATFORM_DIR/rules/writ.mdc")
    rule_baseline=$(manifest_hash_for "rules/writ.mdc")

    if [ "$rule_local" != "$rule_upstream" ]; then
      if [ "$FORCE" = true ]; then
        RULE_ACTION="update"
        echo "    🔄 Update:    rules/writ.mdc (forced)"
      elif [ -z "$rule_baseline" ] || [ "$rule_local" = "$rule_baseline" ]; then
        RULE_ACTION="update"
        echo "    🔄 Update:    rules/writ.mdc"
      else
        RULE_ACTION="preserved"
        echo "    ⚡ Preserved: rules/writ.mdc (local modifications)"
        TOTAL_PRESERVED=$((TOTAL_PRESERVED + 1))
        ALL_PRESERVED_FILES="${ALL_PRESERVED_FILES}    rules/writ.mdc\n"
      fi
    fi
  else
    RULE_ACTION="new"
    echo "    ✨ New:       rules/writ.mdc"
  fi

  SYSINST_ACTION="unchanged"
  if [ -f "$PLATFORM_DIR/system-instructions.md" ]; then
    si_upstream=$(hash_file "$WRIT_SRC/system-instructions.md")
    si_local=$(hash_file "$PLATFORM_DIR/system-instructions.md")
    si_baseline=$(manifest_hash_for "system-instructions.md")

    if [ "$si_local" != "$si_upstream" ]; then
      if [ "$FORCE" = true ]; then
        SYSINST_ACTION="update"
        echo "    🔄 Update:    system-instructions.md (forced)"
      elif [ -z "$si_baseline" ] || [ "$si_local" = "$si_baseline" ]; then
        SYSINST_ACTION="update"
        echo "    🔄 Update:    system-instructions.md"
      else
        SYSINST_ACTION="preserved"
        echo "    ⚡ Preserved: system-instructions.md (local modifications)"
        TOTAL_PRESERVED=$((TOTAL_PRESERVED + 1))
        ALL_PRESERVED_FILES="${ALL_PRESERVED_FILES}    system-instructions.md\n"
      fi
    fi
  elif [ -f "$WRIT_SRC/system-instructions.md" ]; then
    SYSINST_ACTION="new"
    echo "    ✨ New:       system-instructions.md"
  fi

elif [ "$PLATFORM" = "claude" ]; then
  CLAUDE_MD_ACTION="unchanged"
  if [ -f "CLAUDE.md" ] && [ -f "$WRIT_SRC/claude-code/CLAUDE.md" ]; then
    claude_upstream=$(hash_file "$WRIT_SRC/claude-code/CLAUDE.md")
    claude_local=$(hash_file "CLAUDE.md")
    claude_baseline=$(manifest_hash_for "CLAUDE.md")

    if [ "$claude_local" != "$claude_upstream" ]; then
      if [ "$FORCE" = true ]; then
        CLAUDE_MD_ACTION="update"
        echo "    🔄 Update:    CLAUDE.md (forced)"
      elif [ -z "$claude_baseline" ] || [ "$claude_local" = "$claude_baseline" ]; then
        CLAUDE_MD_ACTION="update"
        echo "    🔄 Update:    CLAUDE.md"
      else
        CLAUDE_MD_ACTION="preserved"
        echo "    ⚡ Preserved: CLAUDE.md (local modifications)"
        TOTAL_PRESERVED=$((TOTAL_PRESERVED + 1))
        ALL_PRESERVED_FILES="${ALL_PRESERVED_FILES}    CLAUDE.md\n"
      fi
    fi
  elif [ ! -f "CLAUDE.md" ] && [ -f "$WRIT_SRC/claude-code/CLAUDE.md" ]; then
    CLAUDE_MD_ACTION="new"
    echo "    ✨ New:       CLAUDE.md"
  fi
fi

# Stale file detection
detect_stale_files

echo ""

# Count actionable changes
ACTIONABLE=$((TOTAL_NEW + TOTAL_UPDATED))
if [ "$PLATFORM" = "cursor" ]; then
  { [ "$RULE_ACTION" = "update" ] || [ "$RULE_ACTION" = "new" ]; } && ACTIONABLE=$((ACTIONABLE + 1))
  { [ "$SYSINST_ACTION" = "update" ] || [ "$SYSINST_ACTION" = "new" ]; } && ACTIONABLE=$((ACTIONABLE + 1))
elif [ "$PLATFORM" = "claude" ]; then
  { [ "$CLAUDE_MD_ACTION" = "update" ] || [ "$CLAUDE_MD_ACTION" = "new" ]; } && ACTIONABLE=$((ACTIONABLE + 1))
fi

# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

if [ "$ACTIONABLE" -eq 0 ] && [ "$STALE_COUNT" -eq 0 ] && [ "$TOTAL_PRESERVED" -eq 0 ]; then
  echo "✅ Already up to date! ($NEW_VERSION)"
  exit 0
fi

if [ "$ACTIONABLE" -eq 0 ] && [ "$STALE_COUNT" -eq 0 ]; then
  echo "✅ Already up to date! ($NEW_VERSION)"
  echo ""
  echo "  ⚠️  $TOTAL_PRESERVED file(s) with local modifications were preserved:"
  printf "%b" "$ALL_PRESERVED_FILES"
  echo ""
  echo "  💡 To reset a file: delete it and re-run update."
  echo "  💡 To force overwrite all: update.sh --force"
  exit 0
fi

[ "$ACTIONABLE" -gt 0 ]       && echo "  $ACTIONABLE file(s) to update"
[ "$STALE_COUNT" -gt 0 ]      && echo "  $STALE_COUNT file(s) removed upstream (will be cleaned up)"
[ "$TOTAL_PRESERVED" -gt 0 ]  && echo "  $TOTAL_PRESERVED file(s) preserved (local modifications)"
echo ""

# ---------------------------------------------------------------------------
# Dry run exit
# ---------------------------------------------------------------------------

if [ "$DRY_RUN" = true ]; then
  echo "🏃 DRY RUN — No changes applied."
  if [ "$STALE_COUNT" -gt 0 ]; then
    echo ""
    echo "  Stale files (removed upstream, would be deleted):"
    printf "%b" "$STALE_FILES" | while IFS= read -r sf; do
      [ -n "$sf" ] && echo "    🗑  $sf"
    done
  fi
  if [ "$TOTAL_PRESERVED" -gt 0 ]; then
    echo ""
    echo "  Locally modified files (would be preserved):"
    printf "%b" "$ALL_PRESERVED_FILES"
    echo ""
    echo "  💡 To reset a file: delete it and re-run update."
    echo "  💡 To force overwrite all: update.sh --force"
  fi
  exit 0
fi

# ---------------------------------------------------------------------------
# Phase 2: Apply
# ---------------------------------------------------------------------------

echo "Updating..."

overlay_scan "$WRIT_SRC/commands" "$PLATFORM_DIR/commands" "commands" "apply"
overlay_scan "$WRIT_SRC/$AGENTS_SRC" "$PLATFORM_DIR/agents" "agents" "apply"

UPDATES=0

if [ "$PLATFORM" = "cursor" ]; then
  if [ "$RULE_ACTION" = "update" ] || [ "$RULE_ACTION" = "new" ]; then
    cp "$WRIT_SRC/cursor/writ.mdc" "$PLATFORM_DIR/rules/"
    UPDATES=$((UPDATES + 1))
  fi
  if [ "$SYSINST_ACTION" = "update" ] || [ "$SYSINST_ACTION" = "new" ]; then
    cp "$WRIT_SRC/system-instructions.md" "$PLATFORM_DIR/"
    UPDATES=$((UPDATES + 1))
  fi
elif [ "$PLATFORM" = "claude" ]; then
  if [ "$CLAUDE_MD_ACTION" = "update" ] || [ "$CLAUDE_MD_ACTION" = "new" ]; then
    cp "$WRIT_SRC/claude-code/CLAUDE.md" "CLAUDE.md"
    UPDATES=$((UPDATES + 1))
  fi
fi

# Remove stale files
STALE_REMOVED=0
if [ "$STALE_COUNT" -gt 0 ]; then
  printf "%b" "$STALE_FILES" | while IFS= read -r sf; do
    [ -z "$sf" ] && continue
    if [ "$sf" = "CLAUDE.md" ]; then
      rm -f "CLAUDE.md"
    else
      rm -f "$PLATFORM_DIR/$sf"
    fi
    echo "  🗑  Removed: $sf"
  done
  STALE_REMOVED=$STALE_COUNT
fi

# Regenerate manifest with new baselines
write_copy_manifest "$NEW_VERSION" "$MANIFEST_FILE"

TOTAL_CHANGES=$((ACTIONABLE + STALE_REMOVED))

echo ""
echo "✅ Writ updated for $PLATFORM_LABEL! ($CURRENT_VERSION → $NEW_VERSION, $TOTAL_CHANGES file(s) changed)"

if [ "$TOTAL_PRESERVED" -gt 0 ]; then
  echo ""
  echo "  ⚠️  $TOTAL_PRESERVED file(s) with local modifications were preserved:"
  printf "%b" "$ALL_PRESERVED_FILES"
  echo ""
  echo "  💡 To reset a file: delete it and re-run update."
  echo "  💡 To force overwrite all: update.sh --force"
fi

# ---------------------------------------------------------------------------
# Scoped git commit
# ---------------------------------------------------------------------------

if [ "$NO_COMMIT" = false ] && command -v git &>/dev/null && [ -d .git ]; then
  git add "$PLATFORM_DIR/commands/" "$PLATFORM_DIR/agents/" "$MANIFEST_FILE" 2>/dev/null || true
  if [ "$PLATFORM" = "cursor" ]; then
    git add "$PLATFORM_DIR/rules/writ.mdc" "$PLATFORM_DIR/system-instructions.md" 2>/dev/null || true
  elif [ "$PLATFORM" = "claude" ]; then
    git add "CLAUDE.md" 2>/dev/null || true
  fi

  git commit -m "$(cat <<EOF
chore: update Writ for $PLATFORM_LABEL ($CURRENT_VERSION → $NEW_VERSION)

Updated from $WRIT_REPO
EOF
)" 2>/dev/null && echo "  📦 Git commit created." || echo "  ℹ️  Nothing to commit."
fi

echo ""
echo "⚡ So it is written. So it shall be built."

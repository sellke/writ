#!/bin/bash
# Writ Unlink — converts a symlinked Writ installation to independent copies
# Run from your project root: bash <(curl -s https://raw.githubusercontent.com/sellke/writ/main/scripts/unlink.sh)
#
# After unlinking, use update.sh to stay current.
#
# Flags:
#   --dry-run      Preview changes without applying
#   --no-commit    Don't auto-commit after conversion

set -euo pipefail

WRIT_REPO="https://github.com/sellke/writ.git"
MANIFEST_FILE=".cursor/.writ-manifest"

DRY_RUN=false
NO_COMMIT=false

for arg in "$@"; do
  case $arg in
    --dry-run)    DRY_RUN=true ;;
    --no-commit)  NO_COMMIT=true ;;
    --help|-h)
      echo "Usage: bash unlink.sh [--dry-run] [--no-commit]"
      echo ""
      echo "Converts a symlinked Writ installation to independent file copies."
      echo "Run from your project root."
      echo ""
      echo "After conversion, use update.sh to stay current."
      echo ""
      echo "Flags:"
      echo "  --dry-run      Preview changes without applying"
      echo "  --no-commit    Don't auto-commit after conversion"
      exit 0
      ;;
  esac
done

echo "⚡ Writ Unlink"
echo "==============="
echo ""

# ---------------------------------------------------------------------------
# Guards
# ---------------------------------------------------------------------------

if [ -f "SKILL.md" ] && [ -d "commands" ] && [ -d "agents" ] && [ -d "scripts" ]; then
  echo "❌ This appears to be the Writ source repository."
  echo "   unlink.sh is for converting linked installations in other projects."
  exit 1
fi

if [ ! -f "$MANIFEST_FILE" ]; then
  echo "❌ No Writ manifest found ($MANIFEST_FILE)."
  echo "   Is Writ installed in this project? Run install.sh first."
  exit 1
fi

# ---------------------------------------------------------------------------
# Check mode
# ---------------------------------------------------------------------------

manifest_mode() {
  if grep -q '^# mode:' "$MANIFEST_FILE"; then
    grep '^# mode:' "$MANIFEST_FILE" | sed 's/^# mode: //'
  else
    echo "copy"
  fi
}

manifest_link_target() {
  grep '^# link_target:' "$MANIFEST_FILE" | sed 's/^# link_target: //' || true
}

manifest_version() {
  grep '^# version:' "$MANIFEST_FILE" | sed 's/^# version: //' || true
}

MODE=$(manifest_mode)

if [ "$MODE" != "link" ]; then
  echo "✅ This is already a copy-based installation. Nothing to do."
  exit 0
fi

LINK_TARGET=$(manifest_link_target)
VERSION=$(manifest_version)

echo "  🔗 Current mode:   linked"
echo "  📂 Link target:    ${LINK_TARGET:-<unknown>}"
echo "  📌 Version:        ${VERSION:-unknown}"
echo ""

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
# Scan symlinks
# ---------------------------------------------------------------------------

SYMLINKS=()
REGULAR=()

scan_file() {
  local f="$1"
  if [ -L "$f" ]; then
    local target
    target=$(readlink "$f" 2>/dev/null || true)
    if [ -n "$target" ] && [ -f "$f" ]; then
      SYMLINKS+=("$f|$target")
    else
      echo "  ⚠️  Broken symlink: $f → ${target:-<unresolvable>}"
    fi
  elif [ -f "$f" ]; then
    REGULAR+=("$f")
  fi
}

for f in .cursor/commands/*.md; do [ -e "$f" ] && scan_file "$f"; done
for f in .cursor/agents/*.md;   do [ -e "$f" ] && scan_file "$f"; done
scan_file ".cursor/rules/writ.mdc"
scan_file ".cursor/system-instructions.md"

# Also check for directory-level symlinks (older link installs)
DIR_SYMLINKS=()
for d in .cursor/commands .cursor/agents; do
  if [ -L "$d" ]; then
    DIR_SYMLINKS+=("$d|$(readlink "$d" 2>/dev/null || true)")
  fi
done

if [ ${#SYMLINKS[@]} -eq 0 ] && [ ${#DIR_SYMLINKS[@]} -eq 0 ]; then
  echo "  No symlinks found — files are already independent copies."
  echo "  Updating manifest to copy mode..."
  if [ "$DRY_RUN" = false ]; then
    # Rewrite manifest as copy mode
    cat > "$MANIFEST_FILE" << EOF
# Writ Manifest — do not edit manually
# Tracks installed file baselines for safe overlay updates.
# mode: copy
# version: ${VERSION:-unknown}
# date: $(date -u +%Y-%m-%dT%H:%M:%SZ)
# source: $WRIT_REPO
EOF
    for f in .cursor/commands/*.md .cursor/agents/*.md; do
      [ -f "$f" ] || continue
      rel="${f#.cursor/}"
      echo "$(hash_file "$f")  $rel" >> "$MANIFEST_FILE"
    done
    for f in .cursor/rules/writ.mdc .cursor/system-instructions.md; do
      [ -f "$f" ] || continue
      rel="${f#.cursor/}"
      echo "$(hash_file "$f")  $rel" >> "$MANIFEST_FILE"
    done
    echo "  ✅ Manifest updated to copy mode."
  else
    echo "  🏃 DRY RUN — Would update manifest to copy mode."
  fi
  exit 0
fi

echo "  Found ${#SYMLINKS[@]} symlinked file(s)"
[ ${#REGULAR[@]} -gt 0 ] && echo "  Found ${#REGULAR[@]} regular file(s) (already copies)"
[ ${#DIR_SYMLINKS[@]} -gt 0 ] && echo "  Found ${#DIR_SYMLINKS[@]} directory symlink(s)"
echo ""

# ---------------------------------------------------------------------------
# Dry run
# ---------------------------------------------------------------------------

if [ "$DRY_RUN" = true ]; then
  echo "🏃 DRY RUN — No changes will be made"
  echo ""
  for entry in "${DIR_SYMLINKS[@]}"; do
    local_path="${entry%%|*}"
    target="${entry##*|}"
    echo "  📁 $local_path → $target (would replace directory symlink with copies)"
  done
  for entry in "${SYMLINKS[@]}"; do
    local_path="${entry%%|*}"
    target="${entry##*|}"
    echo "  📄 $local_path → $target"
  done
  echo ""
  echo "  Would convert ${#SYMLINKS[@]} symlink(s) to independent copies"
  echo "  and rewrite manifest from link → copy mode."
  exit 0
fi

# ---------------------------------------------------------------------------
# Convert
# ---------------------------------------------------------------------------

echo "Converting..."
CONVERTED=0

# Handle directory symlinks first (older link installs)
for entry in "${DIR_SYMLINKS[@]}"; do
  local_path="${entry%%|*}"
  target="${entry##*|}"
  echo "  📁 Replacing directory symlink: $local_path"
  rm -f "$local_path"
  mkdir -p "$local_path"
  if [ -d "$target" ]; then
    for f in "$target"/*.md; do
      [ -f "$f" ] || continue
      cp "$f" "$local_path/$(basename "$f")"
      CONVERTED=$((CONVERTED + 1))
    done
  fi
done

# Handle per-file symlinks
for entry in "${SYMLINKS[@]}"; do
  local_path="${entry%%|*}"
  target="${entry##*|}"

  # cp -L follows symlinks; write to temp then atomic replace
  tmp="${local_path}.unlink-tmp"
  cp -L "$local_path" "$tmp"
  rm -f "$local_path"
  mv "$tmp" "$local_path"
  CONVERTED=$((CONVERTED + 1))
done

# ---------------------------------------------------------------------------
# Rewrite manifest
# ---------------------------------------------------------------------------

echo "  Writing manifest (copy mode)..."

cat > "$MANIFEST_FILE" << EOF
# Writ Manifest — do not edit manually
# Tracks installed file baselines for safe overlay updates.
# mode: copy
# version: ${VERSION:-unknown}
# date: $(date -u +%Y-%m-%dT%H:%M:%SZ)
# source: $WRIT_REPO
EOF

for f in .cursor/commands/*.md .cursor/agents/*.md; do
  [ -f "$f" ] || continue
  rel="${f#.cursor/}"
  echo "$(hash_file "$f")  $rel" >> "$MANIFEST_FILE"
done
for f in .cursor/rules/writ.mdc .cursor/system-instructions.md; do
  [ -f "$f" ] || continue
  rel="${f#.cursor/}"
  echo "$(hash_file "$f")  $rel" >> "$MANIFEST_FILE"
done

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

echo ""
echo "✅ Converted $CONVERTED symlink(s) to independent copies."
[ ${#REGULAR[@]} -gt 0 ] && echo "   ${#REGULAR[@]} file(s) were already regular files."
echo ""
echo "  Your installation is now self-contained and git-portable."
echo "  Use update.sh to pull future Writ updates."

# ---------------------------------------------------------------------------
# Git commit
# ---------------------------------------------------------------------------

if [ "$NO_COMMIT" = false ] && command -v git &>/dev/null && [ -d .git ]; then
  git add \
    .cursor/commands/ .cursor/agents/ .cursor/rules/writ.mdc \
    .cursor/system-instructions.md "$MANIFEST_FILE" 2>/dev/null || true

  git commit -m "$(cat <<'EOF'
chore: convert Writ from linked to copied installation

Replaced symlinks with independent file copies. Future updates
will use update.sh with three-way overlay merge.

See: https://github.com/sellke/writ
EOF
)" 2>/dev/null && echo "  📦 Git commit created." || echo "  ℹ️  Nothing to commit."
fi

echo ""
echo "⚡ So it is written. So it shall be built."

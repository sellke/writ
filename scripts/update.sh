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
#   --platform   Target platform: cursor (default), claude, or codex

set -euo pipefail

WRIT_REPO="${WRIT_REPO:-https://github.com/sellke/writ.git}"

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
      echo "Usage: bash update.sh [--dry-run] [--no-commit] [--force] [--platform cursor|claude|codex]"
      echo ""
      echo "Updates Writ commands, agents, and rules from latest GitHub release."
      echo "Run from your project root."
      echo ""
      echo "Platforms:"
      echo "  cursor (default)  Update .cursor/ installation"
      echo "  claude            Update .claude/ installation"
      echo "  codex             Update .codex/ installation and AGENTS.md Writ block"
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
    if [ "$PLATFORM" != "cursor" ] && [ "$PLATFORM" != "claude" ] && [ "$PLATFORM" != "codex" ]; then
      echo "❌ Unknown platform: $PLATFORM"
      echo "   Supported: cursor, claude, codex"
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
  SKILLS_DIR=".cursor/skills"
  AGENT_FILE_GLOB="*.md"
elif [ "$PLATFORM" = "claude" ]; then
  PLATFORM_DIR=".claude"
  MANIFEST_FILE=".claude/.writ-manifest"
  AGENTS_SRC="claude-code/agents"
  PLATFORM_LABEL="Claude Code"
  SKILLS_DIR=".claude/skills"
  AGENT_FILE_GLOB="*.md"
elif [ "$PLATFORM" = "codex" ]; then
  PLATFORM_DIR=".codex"
  MANIFEST_FILE=".codex/.writ-manifest"
  AGENTS_SRC="codex/agents"
  PLATFORM_LABEL="Codex CLI"
  SKILLS_DIR=".agents/skills"
  AGENT_FILE_GLOB="*.toml"
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
elif [ "$PLATFORM" = "codex" ]; then
  if [ ! -d "$PLATFORM_DIR/commands" ] || [ ! -f "$MANIFEST_FILE" ]; then
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
  if [ -f "scripts/recommend-state.py" ]; then
    echo "$(hash_file "scripts/recommend-state.py")  scripts/recommend-state.py" >> "$target"
  fi
  if [ -f ".writ/docs/recommended-delivery-state-format.md" ]; then
    echo "$(hash_file ".writ/docs/recommended-delivery-state-format.md")  .writ/docs/recommended-delivery-state-format.md" >> "$target"
  fi
  for f in "$PLATFORM_DIR"/commands/*.md; do
    [ -f "$f" ] || continue
    rel="${f#"$PLATFORM_DIR"/}"
    echo "$(hash_file "$f")  $rel" >> "$target"
  done

  if [ "$PLATFORM" = "codex" ]; then
    for f in "$PLATFORM_DIR"/agents/*.toml; do
      [ -f "$f" ] || continue
      rel="${f#"$PLATFORM_DIR"/}"
      echo "$(hash_file "$f")  $rel" >> "$target"
    done
  else
    for f in "$PLATFORM_DIR"/agents/*.md; do
      [ -f "$f" ] || continue
      rel="${f#"$PLATFORM_DIR"/}"
      echo "$(hash_file "$f")  $rel" >> "$target"
    done
  fi

  local skill_folder skill_name src_skill
  if [ -d "$SKILLS_DIR" ]; then
    for skill_folder in "$SKILLS_DIR"/*/; do
      [ -d "$skill_folder" ] || continue
      skill_name=$(basename "$skill_folder")
      src_skill="${skill_folder}SKILL.md"
      [ -f "$src_skill" ] || continue
      rel="skills/$skill_name/SKILL.md"
      echo "$(hash_file "$src_skill")  $rel" >> "$target"
    done
  fi

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

  if [ "$PLATFORM" = "codex" ]; then
    local iw config_baseline
    if [ -f "AGENTS.md" ] && iw="$(writ_compute_writ_block_inner_hash "AGENTS.md")"; then
      echo "$iw  AGENTS.md.writ-block" >> "$target"
    fi
    config_baseline=$(manifest_hash_for ".codex/config.toml.baseline")
    if [ -n "$config_baseline" ]; then
      echo "$config_baseline  .codex/config.toml.baseline" >> "$target"
    fi
  fi
}

writ_block_marker_counts() {
  local file="$1"
  awk '{
      line=$0
      sub(/\r$/, "", line)
      if (line == "<!-- writ:start -->") starts++
      if (line == "<!-- writ:end -->") ends++
    }
    END { print starts + 0, ends + 0 }' "$file"
}

writ_compute_writ_block_inner_hash() {
  local file="$1"
  local tmp ec inner_hash_val
  tmp=$(mktemp)
  awk 'BEGIN { starts=0; ends=0; capturing=0; seen_end=0 }
    {
      line=$0
      sub(/\r$/, "", line)
      if (line == "<!-- writ:start -->") {
        starts++
        if (capturing==1 || seen_end==1) { exit 2 }
        capturing=1
        next
      }
      if (line == "<!-- writ:end -->") {
        ends++
        if (capturing!=1) { exit 2 }
        capturing=0
        seen_end=1
        next
      }
      if (capturing==1) print
    }
    END {
      if (starts!=1 || ends!=1 || capturing==1) exit 2
    }' "$file" >"$tmp"
  ec=$?
  if [ "$ec" -ne 0 ]; then
    rm -f "$tmp"
    return "$ec"
  fi
  inner_hash_val="$(hash_file "$tmp")"
  rm -f "$tmp"
  printf '%s\n' "${inner_hash_val:-}"
}

writ_file_ends_with_newline() {
  local file="$1"
  local last_hex
  [ -s "$file" ] || return 0
  last_hex=$(tail -c 1 "$file" | od -An -t x1 | tr -d ' \n')
  [ "$last_hex" = "0a" ]
}

writ_rewrite_agents_md_with_inner() {
  local file="$1"
  local new_inner="$2"
  local staging start_line end_line
  staging=$(mktemp)
  read -r start_line end_line <<<"$(awk '{
      line=$0
      sub(/\r$/, "", line)
      if (line == "<!-- writ:start -->") printf "%d ", NR
      if (line == "<!-- writ:end -->") print NR
    }' "$file")"
  [ -n "${start_line:-}" ] && [ -n "${end_line:-}" ] && [ "$start_line" -lt "$end_line" ] || {
    rm -f "$staging"
    return 1
  }
  if [ "$start_line" -gt 1 ]; then
    head -n $((start_line - 1)) "$file" >"$staging"
  else
    : >"$staging"
  fi
  printf '%s\n' '<!-- writ:start -->' >>"$staging"
  printf '%s\n' "$new_inner" >>"$staging"
  printf '%s\n' '<!-- writ:end -->' >>"$staging"
  tail -n +$((end_line + 1)) "$file" >>"$staging"
  mv "$staging" "$file"
}

merge_agents_md() {
  local mode="${1:-preview}"
  local template="$WRIT_SRC/codex/AGENTS.md.template"
  local agents_md="AGENTS.md"
  AGENTS_MD_ACTION="unchanged"
  AGENTS_MD_NOTE=""

  [ -f "$template" ] || {
    AGENTS_MD_ACTION="error"
    AGENTS_MD_NOTE="AGENTS.md: Writ block error: missing codex/AGENTS.md.template"
    echo "    ❌ $AGENTS_MD_NOTE"
    return 12
  }

  local upstream_inner upstream_hash
  upstream_inner=$(cat "$template")
  upstream_hash=$(hash_file "$template")

  if [ ! -f "$agents_md" ]; then
    AGENTS_MD_ACTION="restore"
    AGENTS_MD_NOTE="AGENTS.md: Writ block re-added"
    [ "$mode" = "preview" ] && echo "    ✨ Restored: AGENTS.md (Writ block re-added)"
    if [ "$mode" = "apply" ]; then
      {
        printf '%s\n' '<!-- writ:start -->'
        printf '%s\n' "$upstream_inner"
        printf '%s\n' '<!-- writ:end -->'
      } >"$agents_md"
    fi
    return 0
  fi

  local counts start_count end_count
  counts=$(writ_block_marker_counts "$agents_md")
  read -r start_count end_count <<<"$counts"

  if [ "${start_count:-0}" -eq 0 ] && [ "${end_count:-0}" -eq 0 ]; then
    AGENTS_MD_ACTION="restore"
    AGENTS_MD_NOTE="AGENTS.md: Writ block re-added"
    [ "$mode" = "preview" ] && echo "    ✨ Restored: AGENTS.md (Writ block re-added)"
    if [ "$mode" = "apply" ]; then
      local tmp
      tmp=$(mktemp)
      cat "$agents_md" >"$tmp"
      if ! writ_file_ends_with_newline "$agents_md"; then
        printf '\n' >>"$tmp"
      fi
      printf '%s\n' '<!-- writ:start -->' >>"$tmp"
      printf '%s\n' "$upstream_inner" >>"$tmp"
      printf '%s\n' '<!-- writ:end -->' >>"$tmp"
      mv "$tmp" "$agents_md"
    fi
    return 0
  fi

  if [ "${start_count:-0}" -ne 1 ] || [ "${end_count:-0}" -ne 1 ]; then
    AGENTS_MD_ACTION="error"
    AGENTS_MD_NOTE="AGENTS.md: Writ block error: malformed markers"
    echo "    ❌ $AGENTS_MD_NOTE"
    return 13
  fi

  local inner_hash baseline_hash
  if ! inner_hash="$(writ_compute_writ_block_inner_hash "$agents_md")"; then
    AGENTS_MD_ACTION="error"
    AGENTS_MD_NOTE="AGENTS.md: Writ block error: malformed markers"
    echo "    ❌ $AGENTS_MD_NOTE"
    return 13
  fi
  baseline_hash=$(manifest_hash_for "AGENTS.md.writ-block")

  if [ "$inner_hash" = "$upstream_hash" ]; then
    AGENTS_MD_ACTION="unchanged"
    AGENTS_MD_NOTE="AGENTS.md: Writ block unchanged"
    return 0
  fi

  if [ "$FORCE" = true ] || { [ -n "$baseline_hash" ] && [ "$inner_hash" = "$baseline_hash" ]; }; then
    AGENTS_MD_ACTION="update"
    AGENTS_MD_NOTE="AGENTS.md: Writ block updated"
    [ "$mode" = "preview" ] && echo "    🔄 Updated: AGENTS.md (Writ block$([ "$FORCE" = true ] && echo " forced"))"
    [ "$mode" = "apply" ] && writ_rewrite_agents_md_with_inner "$agents_md" "$upstream_inner"
    return 0
  fi

  AGENTS_MD_ACTION="preserved"
  AGENTS_MD_NOTE="AGENTS.md: Writ block preserved (local modifications)"
  echo "    ⚡ Preserved: AGENTS.md (Writ block has local modifications)"
  return 0
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
  local src_dir="$1" local_dir="$2" label="$3" mode="$4" pattern="${5:-*.md}"
  _NEW=0; _UPDATED=0; _PRESERVED=0; _UNCHANGED=0
  _PRESERVED_FILES=""

  local src_file fname local_file rel_path upstream_hash local_hash baseline_hash
  for src_file in "$src_dir"/$pattern; do
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

scan_helper() {
  local src="$WRIT_SRC/scripts/recommend-state.py"
  local dest="scripts/recommend-state.py"
  HELPER_ACTION="unchanged"
  [ -f "$src" ] || { echo "    ❌ Missing upstream scripts/recommend-state.py"; return 15; }
  if [ ! -f "$dest" ]; then
    HELPER_ACTION="new"
    echo "    ✨ New:       scripts/recommend-state.py"
    return 0
  fi
  local upstream_hash local_hash baseline_hash
  upstream_hash=$(hash_file "$src")
  local_hash=$(hash_file "$dest")
  [ "$upstream_hash" = "$local_hash" ] && return 0
  baseline_hash=$(manifest_hash_for "scripts/recommend-state.py")
  if [ "$FORCE" = true ] || { [ -n "$baseline_hash" ] && [ "$local_hash" = "$baseline_hash" ]; }; then
    HELPER_ACTION="update"
    echo "    🔄 Update:    scripts/recommend-state.py"
  else
    HELPER_ACTION="preserved"
    echo "    ⚡ Preserved: scripts/recommend-state.py (local modifications)"
  fi
}

apply_helper() {
  if [ "$HELPER_ACTION" = "new" ] || [ "$HELPER_ACTION" = "update" ]; then
    mkdir -p scripts
    cp "$WRIT_SRC/scripts/recommend-state.py" "scripts/recommend-state.py"
    chmod 755 "scripts/recommend-state.py"
  fi
}

scan_state_doc() {
  local src="$WRIT_SRC/.writ/docs/recommended-delivery-state-format.md"
  local dest=".writ/docs/recommended-delivery-state-format.md"
  STATE_DOC_ACTION="unchanged"
  [ -f "$src" ] || { echo "    ❌ Missing upstream $dest"; return 15; }
  if [ ! -f "$dest" ]; then
    STATE_DOC_ACTION="new"
    echo "    ✨ New:       $dest"
    return 0
  fi
  local upstream_hash local_hash baseline_hash
  upstream_hash=$(hash_file "$src")
  local_hash=$(hash_file "$dest")
  [ "$upstream_hash" = "$local_hash" ] && return 0
  baseline_hash=$(manifest_hash_for "$dest")
  if [ "$FORCE" = true ] || { [ -n "$baseline_hash" ] && [ "$local_hash" = "$baseline_hash" ]; }; then
    STATE_DOC_ACTION="update"
    echo "    🔄 Update:    $dest"
  else
    STATE_DOC_ACTION="preserved"
    echo "    ⚡ Preserved: $dest (local modifications)"
  fi
}

apply_state_doc() {
  if [ "$STATE_DOC_ACTION" = "new" ] || [ "$STATE_DOC_ACTION" = "update" ]; then
    mkdir -p ".writ/docs"
    cp "$WRIT_SRC/.writ/docs/recommended-delivery-state-format.md" \
      ".writ/docs/recommended-delivery-state-format.md"
  fi
}

# Skills overlay — folder-aware, SKILL.md hash-tracked, sidecar files install-once.
overlay_scan_skills() {
  local src_dir="$1" local_dir="$2" mode="$3"
  _NEW=0; _UPDATED=0; _PRESERVED=0; _UNCHANGED=0
  _PRESERVED_FILES=""

  local skill_folder skill_name src_skill local_skill rel_path upstream_hash local_hash baseline_hash
  local sidecar sidecar_name
  for skill_folder in "$src_dir"/*/; do
    [ -d "$skill_folder" ] || continue
    skill_name=$(basename "$skill_folder")
    src_skill="${skill_folder}SKILL.md"
    [ -f "$src_skill" ] || continue

    local_skill="$local_dir/$skill_name/SKILL.md"
    rel_path="skills/$skill_name/SKILL.md"
    upstream_hash=$(hash_file "$src_skill")

    if [ ! -f "$local_skill" ]; then
      _NEW=$((_NEW + 1))
      if [ "$mode" = "preview" ]; then echo "    ✨ New:       $rel_path"; fi
      if [ "$mode" = "apply" ]; then
        mkdir -p "$local_dir/$skill_name"
        cp "$src_skill" "$local_skill"
        for sidecar in "$skill_folder".[!.]* "$skill_folder"*; do
          [ -e "$sidecar" ] || continue
          sidecar_name=$(basename "$sidecar")
          [ "$sidecar_name" = "SKILL.md" ] && continue
          [ -d "$sidecar" ] && continue
          cp "$sidecar" "$local_dir/$skill_name/$sidecar_name"
        done
      fi
      continue
    fi

    local_hash=$(hash_file "$local_skill")

    if [ "$local_hash" = "$upstream_hash" ]; then
      _UNCHANGED=$((_UNCHANGED + 1))
      continue
    fi

    baseline_hash=$(manifest_hash_for "$rel_path")

    if [ "$FORCE" = true ]; then
      _UPDATED=$((_UPDATED + 1))
      if [ "$mode" = "preview" ]; then echo "    🔄 Update:    $rel_path (forced)"; fi
      if [ "$mode" = "apply" ];   then cp "$src_skill" "$local_skill"; fi
    elif [ -z "$baseline_hash" ]; then
      _PRESERVED=$((_PRESERVED + 1))
      _PRESERVED_FILES="${_PRESERVED_FILES}    ${rel_path}\n"
      if [ "$mode" = "preview" ]; then echo "    ⚡ Preserved: $rel_path (no baseline, assuming modified)"; fi
    elif [ "$local_hash" = "$baseline_hash" ]; then
      _UPDATED=$((_UPDATED + 1))
      if [ "$mode" = "preview" ]; then echo "    🔄 Update:    $rel_path"; fi
      if [ "$mode" = "apply" ];   then cp "$src_skill" "$local_skill"; fi
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

    # CLAUDE.md lives at project root, not inside the platform dir.
    if [ "$manifest_path" = "CLAUDE.md" ]; then
      local_file="CLAUDE.md"
    elif [ "${manifest_path%%/*}" = "skills" ]; then
      local_file="$SKILLS_DIR/${manifest_path#skills/}"
    elif [ "$manifest_path" = "AGENTS.md.writ-block" ] || [ "$manifest_path" = ".codex/config.toml.baseline" ]; then
      continue
    elif [ "${manifest_path%%/*}" = ".writ" ]; then
      local_file="$manifest_path"
    else
      local_file="$PLATFORM_DIR/$manifest_path"
    fi
    [ -f "$local_file" ] || continue

    category="${manifest_path%%/*}"
    case "$category" in
      commands) upstream_file="$WRIT_SRC/commands/$(basename "$manifest_path")" ;;
      agents)   upstream_file="$WRIT_SRC/$AGENTS_SRC/$(basename "$manifest_path")" ;;
      skills)
        # manifest_path looks like: skills/<name>/SKILL.md
        skill_subpath="${manifest_path#skills/}"
        upstream_file="$WRIT_SRC/skills/$skill_subpath"
        ;;
      scripts)  upstream_file="$WRIT_SRC/$manifest_path"; local_file="$manifest_path" ;;
      .writ)    upstream_file="$WRIT_SRC/$manifest_path"; local_file="$manifest_path" ;;
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

echo "  Runtime helper:"
scan_helper
case "$HELPER_ACTION" in
  new) TOTAL_NEW=$((TOTAL_NEW + 1)) ;;
  update) TOTAL_UPDATED=$((TOTAL_UPDATED + 1)) ;;
  preserved)
    TOTAL_PRESERVED=$((TOTAL_PRESERVED + 1))
    ALL_PRESERVED_FILES="${ALL_PRESERVED_FILES}    scripts/recommend-state.py\n"
    ;;
esac

echo "  Runtime contract:"
scan_state_doc
case "$STATE_DOC_ACTION" in
  new) TOTAL_NEW=$((TOTAL_NEW + 1)) ;;
  update) TOTAL_UPDATED=$((TOTAL_UPDATED + 1)) ;;
  preserved)
    TOTAL_PRESERVED=$((TOTAL_PRESERVED + 1))
    ALL_PRESERVED_FILES="${ALL_PRESERVED_FILES}    .writ/docs/recommended-delivery-state-format.md\n"
    ;;
esac

echo "  Agents:"
overlay_scan "$WRIT_SRC/$AGENTS_SRC" "$PLATFORM_DIR/agents" "agents" "preview" "$AGENT_FILE_GLOB"
TOTAL_NEW=$((TOTAL_NEW + _NEW))
TOTAL_UPDATED=$((TOTAL_UPDATED + _UPDATED))
TOTAL_PRESERVED=$((TOTAL_PRESERVED + _PRESERVED))
ALL_PRESERVED_FILES="${ALL_PRESERVED_FILES}${_PRESERVED_FILES}"
AGENT_UNCHANGED=$_UNCHANGED

SKILL_UNCHANGED=0
if [ -d "$WRIT_SRC/skills" ]; then
  has_skills=false
  for d in "$WRIT_SRC/skills"/*/; do
    [ -d "$d" ] && [ -f "${d}SKILL.md" ] && { has_skills=true; break; }
  done
  if [ "$has_skills" = true ]; then
    mkdir -p "$SKILLS_DIR"
    echo "  Skills:"
    overlay_scan_skills "$WRIT_SRC/skills" "$SKILLS_DIR" "preview"
    TOTAL_NEW=$((TOTAL_NEW + _NEW))
    TOTAL_UPDATED=$((TOTAL_UPDATED + _UPDATED))
    TOTAL_PRESERVED=$((TOTAL_PRESERVED + _PRESERVED))
    ALL_PRESERVED_FILES="${ALL_PRESERVED_FILES}${_PRESERVED_FILES}"
    SKILL_UNCHANGED=$_UNCHANGED
  fi
fi

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
elif [ "$PLATFORM" = "codex" ]; then
  echo "  AGENTS.md:"
  merge_agents_md preview
  case "$AGENTS_MD_ACTION" in
    preserved)
      TOTAL_PRESERVED=$((TOTAL_PRESERVED + 1))
      ALL_PRESERVED_FILES="${ALL_PRESERVED_FILES}    AGENTS.md (Writ block)\n"
      ;;
  esac
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
elif [ "$PLATFORM" = "codex" ]; then
  { [ "${AGENTS_MD_ACTION:-unchanged}" = "update" ] || [ "${AGENTS_MD_ACTION:-unchanged}" = "restore" ]; } && ACTIONABLE=$((ACTIONABLE + 1))
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
apply_helper
apply_state_doc
overlay_scan "$WRIT_SRC/$AGENTS_SRC" "$PLATFORM_DIR/agents" "agents" "apply" "$AGENT_FILE_GLOB"

if [ -d "$WRIT_SRC/skills" ]; then
  has_skills=false
  for d in "$WRIT_SRC/skills"/*/; do
    [ -d "$d" ] && [ -f "${d}SKILL.md" ] && { has_skills=true; break; }
  done
  if [ "$has_skills" = true ]; then
    mkdir -p "$SKILLS_DIR"
    overlay_scan_skills "$WRIT_SRC/skills" "$SKILLS_DIR" "apply"
  fi
fi

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
elif [ "$PLATFORM" = "codex" ]; then
  if [ "$AGENTS_MD_ACTION" = "update" ] || [ "$AGENTS_MD_ACTION" = "restore" ]; then
    merge_agents_md apply
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
  git add "scripts/recommend-state.py" 2>/dev/null || true
  git add "$PLATFORM_DIR/commands/" "$PLATFORM_DIR/agents/" "$MANIFEST_FILE" 2>/dev/null || true
  [ -d "$SKILLS_DIR" ] && git add "$SKILLS_DIR/" 2>/dev/null || true
  if [ "$PLATFORM" = "cursor" ]; then
    git add "$PLATFORM_DIR/rules/writ.mdc" "$PLATFORM_DIR/system-instructions.md" 2>/dev/null || true
  elif [ "$PLATFORM" = "claude" ]; then
    git add "CLAUDE.md" 2>/dev/null || true
  elif [ "$PLATFORM" = "codex" ]; then
    git add "AGENTS.md" 2>/dev/null || true
  fi

  git commit -m "$(cat <<EOF
chore: update Writ for $PLATFORM_LABEL ($CURRENT_VERSION → $NEW_VERSION)

Updated from $WRIT_REPO
EOF
)" 2>/dev/null && echo "  📦 Git commit created." || echo "  ℹ️  Nothing to commit."
fi

echo ""
echo "⚡ So it is written. So it shall be built."

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
      echo "Updates Writ commands, agents, runtime scripts, Writ docs, and rules from latest GitHub release."
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

# Baselines this run trusts, one "<hash>  <path>" line each. load_baselines
# fills it after the clone; until then lookups read the manifest itself.
BASELINES_FILE=""
# Set by load_legacy_baselines when a legacy manifest's version cannot be
# used: the reason, for the notice printed after the version lines.
LEGACY_FALLBACK_REASON=""

# load_baselines — the one place that decides which baselines this run trusts.
# A manifest with `# baselines: shipped`: its "<hash>  <path>" lines. A legacy
# manifest: baselines rebuilt by load_legacy_baselines. No manifest: none.
# write_copy_manifest truncates the manifest, so lookups read this copy
# instead.
load_baselines() {
  BASELINES_FILE=$(mktemp)
  [ -f "$MANIFEST_FILE" ] || return 0
  if grep -qx '# baselines: shipped' "$MANIFEST_FILE"; then
    awk '!/^#/ && NF' "$MANIFEST_FILE" > "$BASELINES_FILE"
  else
    load_legacy_baselines
  fi
}

# The upstream source path of a manifest path. Fails for a path Writ does not
# ship under that name, such as an old whole-file CLAUDE.md line.
legacy_source_path() {
  case "$1" in
    commands/*|skills/*/SKILL.md|scripts/*|.writ/docs/*|system-instructions.md)
      printf '%s\n' "$1" ;;
    agents/*)             printf '%s/%s\n' "$AGENTS_SRC" "${1#agents/}" ;;
    rules/writ.mdc)       printf 'cursor/writ.mdc\n' ;;
    CLAUDE.md.writ-block) printf 'claude-code/CLAUDE.md\n' ;;
    AGENTS.md.writ-block) printf 'codex/AGENTS.md.template\n' ;;
    *) return 1 ;;
  esac
}

# Print the full commit id of a manifest version in the upstream clone. The
# version comes from a file in the project, so accept only a hex id: it can
# never be read as a git option. A shallow clone lacks older commits, so fetch
# the full history once and look again. Every failure returns 1.
legacy_resolve_commit() {
  local v="$1"
  case "$v" in
    *[!0123456789abcdef]*) return 1 ;;
  esac
  [ "${#v}" -ge 4 ] && [ "${#v}" -le 40 ] || return 1
  git -C "$WRIT_SRC" rev-parse -q --verify "$v^{commit}" 2>/dev/null && return 0
  [ "$(git -C "$WRIT_SRC" rev-parse --is-shallow-repository 2>/dev/null)" = "true" ] || return 1
  git -C "$WRIT_SRC" fetch --quiet --unshallow >/dev/null 2>&1 || return 1
  git -C "$WRIT_SRC" rev-parse -q --verify "$v^{commit}" 2>/dev/null
}

# A manifest without `# baselines: shipped` was written by a pre-fix script
# (Business Rule 9). It can record user files, and customizations re-baselined
# to their local hash. Rebuild its baselines from upstream at its `# version:`:
# each path gets the hash of its source file at that commit, and a path
# upstream did not have then is a user file and gets no line, so it is never
# stale. The Codex config line is kept as recorded. When the version cannot be
# found, keep only that line: every file that differs from upstream then has
# no baseline and is preserved, and nothing is stale, as with no manifest.
load_legacy_baselines() {
  local v commit path src blob
  awk '!/^#/ && $2 == ".codex/config.toml.baseline" { print; exit }' "$MANIFEST_FILE" > "$BASELINES_FILE"
  v=$(manifest_version | sed -n '1p')
  if [ -z "$v" ] || [ "$v" = "unknown" ]; then
    LEGACY_FALLBACK_REASON="its version is unknown"
    return 0
  fi
  if ! commit=$(legacy_resolve_commit "$v"); then
    LEGACY_FALLBACK_REASON="version $v was not found upstream"
    return 0
  fi
  # Hash a temp copy of each blob with hash_file, so it matches the hashes
  # the overlay computes from the clone's files. For a Writ block that is the
  # template's hash, which the merge functions compare the inner hash with.
  blob=$(mktemp)
  while IFS= read -r path; do
    [ -n "$path" ] || continue
    src=$(legacy_source_path "$path") || continue
    git -C "$WRIT_SRC" cat-file blob "$commit:$src" > "$blob" 2>/dev/null || continue
    printf '%s  %s\n' "$(hash_file "$blob")" "$path" >> "$BASELINES_FILE"
  done <<< "$(awk '!/^#/ && NF && $2 != ".codex/config.toml.baseline" && !seen[$2]++ { print $2 }' "$MANIFEST_FILE")"
  rm -f "$blob"
}

baselines_source() {
  if [ -n "${BASELINES_FILE:-}" ]; then
    printf '%s\n' "$BASELINES_FILE"
  else
    printf '%s\n' "$MANIFEST_FILE"
  fi
}

# The recorded hash for one path. Exact match on the path field; first line wins.
manifest_hash_for() {
  local path="$1" source
  source=$(baselines_source)
  [ -f "$source" ] || return 0
  awk -v p="$path" '!/^#/ && $2 == p { print $1; exit }' "$source"
}

manifest_files() {
  local source
  source=$(baselines_source)
  [ -f "$source" ] || return 0
  awk '!/^#/ && NF { print $2 }' "$source"
}

# record_file_baseline — append the manifest line for one shipped file
# (Business Rule 3). Local copy equals upstream: the upstream hash. Local copy
# differs (the overlay preserved it): its previous baseline, or no line when it
# had none, so a later upstream change is still a preserve. No local copy, or
# nothing upstream: no line. Never writes an empty hash.
record_file_baseline() {
  local target="$1" path="$2" upstream_file="$3" local_file="$4" hash
  [ -f "$local_file" ] && [ -f "$upstream_file" ] || return 0
  if cmp -s "$local_file" "$upstream_file"; then
    hash=$(hash_file "$upstream_file")
  else
    hash=$(manifest_hash_for "$path")
  fi
  [ -n "$hash" ] || return 0
  printf '%s  %s\n' "$hash" "$path" >> "$target"
}

write_copy_manifest() {
  local version="$1" target="$2"

  # The Codex config is install-once and may be edited, so its baseline cannot
  # be recomputed from disk: carry the recorded one. Read it before the
  # truncation below, in case lookups still read the manifest itself (no
  # load_baselines yet). Same order as unlink.sh.
  local config_baseline=""
  if [ "$PLATFORM" = "codex" ]; then
    config_baseline=$(manifest_hash_for ".codex/config.toml.baseline")
  fi

  # `# baselines: shipped` marks a manifest that records only shipped paths
  # (Business Rule 2). A manifest without it was written by an older script.
  cat > "$target" << EOF
# Writ Manifest — do not edit manually
# Tracks installed file baselines for safe overlay updates.
# baselines: shipped
# mode: copy
# platform: $PLATFORM
# version: $version
# date: $(date -u +%Y-%m-%dT%H:%M:%SZ)
# source: $WRIT_REPO
EOF

  # Walk the shipped set in $WRIT_SRC with the overlay scans' own filters,
  # never the project's folders (Business Rule 1): a user's own file in a
  # tracked folder gets no line, so it is never stale and never removed.
  # AGENTS_SRC and AGENT_FILE_GLOB default to empty because
  # test_update_claude_md.sh runs this function by itself without them.
  local f name agents_dir skill_folder skill_name line path
  append_manifest_shippable_scripts "$target"
  append_manifest_writ_docs "$target"
  for f in "$WRIT_SRC"/commands/*.md; do
    [ -f "$f" ] || continue
    name=$(basename "$f")
    record_file_baseline "$target" "commands/$name" "$f" "$PLATFORM_DIR/commands/$name"
  done
  agents_dir="$WRIT_SRC/${AGENTS_SRC:-}"
  for f in "$agents_dir"/${AGENT_FILE_GLOB:-}; do
    [ -f "$f" ] || continue
    name=$(basename "$f")
    record_file_baseline "$target" "agents/$name" "$f" "$PLATFORM_DIR/agents/$name"
  done

  for skill_folder in "$WRIT_SRC"/skills/*/; do
    [ -f "${skill_folder}SKILL.md" ] || continue
    skill_name=$(basename "$skill_folder")
    record_file_baseline "$target" "skills/$skill_name/SKILL.md" \
      "${skill_folder}SKILL.md" "$SKILLS_DIR/$skill_name/SKILL.md"
  done

  # Platform files copied whole.
  if [ "$PLATFORM" = "cursor" ]; then
    record_file_baseline "$target" "rules/writ.mdc" \
      "$WRIT_SRC/cursor/writ.mdc" "$PLATFORM_DIR/rules/writ.mdc"
  fi
  if [ "$PLATFORM" = "cursor" ] || [ "$PLATFORM" = "claude" ]; then
    record_file_baseline "$target" "system-instructions.md" \
      "$WRIT_SRC/system-instructions.md" "$PLATFORM_DIR/system-instructions.md"
  fi

  # Writ block: the inner hash when it equals the template hash the merge
  # functions compare against. Otherwise the block was preserved: keep its
  # previous baseline, or write no line. The same rule as
  # record_file_baseline, kept inline because test_update_claude_md.sh runs
  # this function without the other helpers.
  local block="" template="" inner="" block_hash=""
  case "$PLATFORM" in
    claude) block="CLAUDE.md"; template="$WRIT_SRC/claude-code/CLAUDE.md" ;;
    codex)  block="AGENTS.md"; template="$WRIT_SRC/codex/AGENTS.md.template" ;;
  esac
  if [ -n "$block" ] && [ -f "$block" ] && [ -f "$template" ]; then
    inner=$(writ_compute_writ_block_inner_hash "$block") || inner=""
    if [ -n "$inner" ] && [ "$inner" = "$(hash_file "$template")" ]; then
      block_hash="$inner"
    else
      block_hash=$(manifest_hash_for "$block.writ-block")
    fi
    if [ -n "$block_hash" ]; then
      echo "$block_hash  $block.writ-block" >> "$target"
    fi
  fi

  if [ "$PLATFORM" = "codex" ] && [ -n "$config_baseline" ]; then
    echo "$config_baseline  .codex/config.toml.baseline" >> "$target"
  fi

  # Keep the old baseline of each kept, locally modified stale file, in every
  # category, so the next update warns again instead of dropping it. A stale
  # path is never in the shipped set walked above, so the check below only
  # skips a path the old manifest listed twice.
  if [ -n "${STALE_KEPT_ENTRIES:-}" ]; then
    while IFS= read -r line; do
      [ -n "$line" ] || continue
      path="${line#*  }"
      awk -v p="$path" '$2 == p { found = 1 } END { exit !found }' "$target" && continue
      echo "$line" >> "$target"
    done <<< "$(printf "%b" "$STALE_KEPT_ENTRIES")"
  fi
}

# <<< writ-merge-bundled-begin (used by scripts/tests/test_update_claude_md.sh — keep synced) >>>
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

# writ_block_inner_has_line FILE LINE — returns 0 when a line between the
# markers equals LINE once its trailing "\r" is stripped. Keep synced with
# install.sh.
writ_block_inner_has_line() {
  local file="$1"
  WRIT_WANT_LINE="$2" awk '{
      line=$0
      sub(/\r$/, "", line)
      if (line == "<!-- writ:start -->") { inside=1; next }
      if (line == "<!-- writ:end -->") { inside=0; next }
      if (inside == 1 && line == ENVIRON["WRIT_WANT_LINE"]) found=1
    }
    END { exit found ? 0 : 1 }' "$file"
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

# merge_claude_md — Claude Code ONLY. Integrates claude-code/CLAUDE.md into CLAUDE.md.
# Structurally a same-file duplicate of merge_agents_md (keep synced) — see Notes in
# .writ/specs/2026-08-13-claude-md-install-merge for why this isn't a shared helper.
# Also a separately-maintained copy of install.sh's own merge_claude_md (keep synced).
# Globals: WRIT_SRC, MANIFEST_FILE, FORCE, CLAUDE_MD_ACTION/CLAUDE_MD_NOTE (set on every path)
merge_claude_md() {
  local mode="${1:-preview}"
  local template="$WRIT_SRC/claude-code/CLAUDE.md"
  local claude_md="CLAUDE.md"
  CLAUDE_MD_ACTION="unchanged"
  CLAUDE_MD_NOTE=""

  [ -f "$template" ] || {
    CLAUDE_MD_ACTION="error"
    CLAUDE_MD_NOTE="CLAUDE.md: Writ block error: missing claude-code/CLAUDE.md template"
    echo "    ❌ $CLAUDE_MD_NOTE"
    return 12
  }

  local upstream_inner upstream_hash
  upstream_inner=$(cat "$template")
  upstream_hash=$(hash_file "$template")

  if [ ! -f "$claude_md" ]; then
    CLAUDE_MD_ACTION="restore"
    CLAUDE_MD_NOTE="CLAUDE.md: Writ block re-added"
    [ "$mode" = "preview" ] && echo "    ✨ Restored: CLAUDE.md (Writ block re-added)"
    if [ "$mode" = "apply" ]; then
      {
        printf '%s\n' '<!-- writ:start -->'
        printf '%s\n' "$upstream_inner"
        printf '%s\n' '<!-- writ:end -->'
      } >"$claude_md"
    fi
    return 0
  fi

  local counts start_count end_count
  counts=$(writ_block_marker_counts "$claude_md")
  read -r start_count end_count <<<"$counts"

  if [ "${start_count:-0}" -eq 0 ] && [ "${end_count:-0}" -eq 0 ]; then
    CLAUDE_MD_ACTION="restore"
    CLAUDE_MD_NOTE="CLAUDE.md: Writ block re-added"
    [ "$mode" = "preview" ] && echo "    ✨ Restored: CLAUDE.md (Writ block re-added)"
    if [ "$mode" = "apply" ]; then
      local tmp
      tmp=$(mktemp)
      cat "$claude_md" >"$tmp"
      if ! writ_file_ends_with_newline "$claude_md"; then
        printf '\n' >>"$tmp"
      fi
      printf '%s\n' '<!-- writ:start -->' >>"$tmp"
      printf '%s\n' "$upstream_inner" >>"$tmp"
      printf '%s\n' '<!-- writ:end -->' >>"$tmp"
      mv "$tmp" "$claude_md"
    fi
    return 0
  fi

  if [ "${start_count:-0}" -ne 1 ] || [ "${end_count:-0}" -ne 1 ]; then
    CLAUDE_MD_ACTION="error"
    CLAUDE_MD_NOTE="CLAUDE.md: Writ block error: malformed markers"
    echo "    ❌ $CLAUDE_MD_NOTE"
    return 13
  fi

  local inner_hash baseline_hash
  if ! inner_hash="$(writ_compute_writ_block_inner_hash "$claude_md")"; then
    CLAUDE_MD_ACTION="error"
    CLAUDE_MD_NOTE="CLAUDE.md: Writ block error: malformed markers"
    echo "    ❌ $CLAUDE_MD_NOTE"
    return 13
  fi
  baseline_hash=$(manifest_hash_for "CLAUDE.md.writ-block")

  if [ "$inner_hash" = "$upstream_hash" ]; then
    CLAUDE_MD_ACTION="unchanged"
    CLAUDE_MD_NOTE="CLAUDE.md: Writ block unchanged"
    return 0
  fi

  if [ "$FORCE" = true ] || { [ -n "$baseline_hash" ] && [ "$inner_hash" = "$baseline_hash" ]; }; then
    CLAUDE_MD_ACTION="update"
    CLAUDE_MD_NOTE="CLAUDE.md: Writ block updated"
    [ "$mode" = "preview" ] && echo "    🔄 Updated: CLAUDE.md (Writ block$([ "$FORCE" = true ] && echo " forced"))"
    [ "$mode" = "apply" ] && writ_rewrite_agents_md_with_inner "$claude_md" "$upstream_inner"
    return 0
  fi

  CLAUDE_MD_ACTION="preserved"
  CLAUDE_MD_NOTE="CLAUDE.md: Writ block preserved (local modifications)"
  echo "    ⚡ Preserved: CLAUDE.md (Writ block has local modifications)"
  if ! writ_block_inner_has_line "$claude_md" "@.claude/system-instructions.md"; then
    printf '%s\n' "⚠️  CLAUDE.md: the preserved Writ block has no @.claude/system-instructions.md line. Add it inside the block, or re-run update.sh --force to replace the block."
  fi
  return 0
}
# <<< writ-merge-bundled-end >>>

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
cleanup() {
  rm -rf "$WRIT_SRC"
  if [ -n "${BASELINES_FILE:-}" ]; then rm -f "$BASELINES_FILE"; fi
}
trap cleanup EXIT
load_baselines

NEW_VERSION=$(cd "$WRIT_SRC" && git log -1 --format="%h" 2>/dev/null || echo "unknown")
NEW_VERSION_LONG=$(cd "$WRIT_SRC" && git log -1 --format="%h %s" 2>/dev/null || echo "unknown")
CURRENT_VERSION=$(manifest_version)

echo "   Installed: ${CURRENT_VERSION:-unknown (no manifest)}"
echo "   Latest:    $NEW_VERSION_LONG"
echo ""

if [ -n "$LEGACY_FALLBACK_REASON" ]; then
  echo "  ⚠️  Manifest predates shipped-only baselines and $LEGACY_FALLBACK_REASON; files that differ from upstream are preserved this run."
  echo ""
elif [ -z "$CURRENT_VERSION" ]; then
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

is_shippable_script() {
  local base="$1"
  case "$base" in
    install.sh|update.sh|uninstall.sh|unlink.sh|migrate.sh|publish-writ-runtime.sh|eval.sh)
      return 1 ;;
    writ-runtime-readme.md)
      return 1 ;;
    eval-*|_*|sweep-*)
      return 1 ;;
    pipeline-baseline.py|measure-invocation.py|harness-cost.py|prune-ledger.py|spawn-cap.py|recommend-state.py|gen-claude-md.py|gen-platform-trees.py)
      # Dev-only tooling (eval.sh, measurement, ADR-013 dormant staging, CLAUDE.md template, platform trees); not agent-facing. ADR-029.
      return 1 ;;
  esac
  case "$base" in
    *.py|*.sh)
      return 0 ;;
    jev-thresholds.json)
      # jev-judge.py's calibrated thresholds; the one data file that ships.
      return 0 ;;
  esac
  return 1
}

# Writ reference docs shipped to installed projects (.writ/docs/).
is_shippable_writ_doc() {
  case "$1" in
    recommended-delivery-state-format.md)
      # ADR-013 dormant staging contract; dev-only with recommend-state.py.
      return 1 ;;
  esac
  return 0
}

overlay_scan_flat_dir() {
  local src_dir="$1" dest_dir="$2" rel_prefix="$3" mode="$4" filter="${5:-}"
  _NEW=0; _UPDATED=0; _PRESERVED=0; _UNCHANGED=0
  _PRESERVED_FILES=""

  local src_file fname local_file rel_path upstream_hash local_hash baseline_hash
  for src_file in "$src_dir"/*; do
    [ -f "$src_file" ] || continue
    fname=$(basename "$src_file")
    if [ "$filter" = "script" ] && ! is_shippable_script "$fname"; then
      continue
    fi
    if [ "$filter" = "doc" ] && ! is_shippable_writ_doc "$fname"; then
      continue
    fi

    local_file="$dest_dir/$fname"
    rel_path="$rel_prefix/$fname"
    upstream_hash=$(hash_file "$src_file")

    if [ ! -f "$local_file" ]; then
      _NEW=$((_NEW + 1))
      if [ "$mode" = "preview" ]; then echo "    ✨ New:       $rel_path"; fi
      if [ "$mode" = "apply" ]; then
        mkdir -p "$dest_dir"
        cp "$src_file" "$local_file"
        case "$fname" in *.py|*.sh) chmod 755 "$local_file" ;; esac
      fi
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
      if [ "$mode" = "apply" ]; then
        cp "$src_file" "$local_file"
        case "$fname" in *.py|*.sh) chmod 755 "$local_file" ;; esac
      fi
    elif [ -z "$baseline_hash" ]; then
      _PRESERVED=$((_PRESERVED + 1))
      _PRESERVED_FILES="${_PRESERVED_FILES}    ${rel_path}\n"
      if [ "$mode" = "preview" ]; then echo "    ⚡ Preserved: $rel_path (no baseline, assuming modified)"; fi
    elif [ "$local_hash" = "$baseline_hash" ]; then
      _UPDATED=$((_UPDATED + 1))
      if [ "$mode" = "preview" ]; then echo "    🔄 Update:    $rel_path"; fi
      if [ "$mode" = "apply" ]; then
        cp "$src_file" "$local_file"
        case "$fname" in *.py|*.sh) chmod 755 "$local_file" ;; esac
      fi
    else
      _PRESERVED=$((_PRESERVED + 1))
      _PRESERVED_FILES="${_PRESERVED_FILES}    ${rel_path}\n"
      if [ "$mode" = "preview" ]; then echo "    ⚡ Preserved: $rel_path (local modifications)"; fi
    fi
  done
}

# Manifest lines for the top-level scripts upstream ships (the overlay's
# "script" filter). Called only by write_copy_manifest.
append_manifest_shippable_scripts() {
  local target="$1" f base
  for f in "$WRIT_SRC"/scripts/*; do
    [ -f "$f" ] || continue
    base=$(basename "$f")
    is_shippable_script "$base" || continue
    record_file_baseline "$target" "scripts/$base" "$f" "scripts/$base"
  done
}

# Manifest lines for the .writ/docs/*.md upstream ships (the overlay's "doc"
# filter). Called only by write_copy_manifest.
append_manifest_writ_docs() {
  local target="$1" f base
  for f in "$WRIT_SRC"/.writ/docs/*.md; do
    [ -f "$f" ] || continue
    base=$(basename "$f")
    is_shippable_writ_doc "$base" || continue
    record_file_baseline "$target" ".writ/docs/$base" "$f" ".writ/docs/$base"
  done
}

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
# "<baseline>  <path>" lines for stale files still on disk after this run:
# locally modified ones that were kept, and ones rm could not remove.
STALE_KEPT_ENTRIES=""

detect_stale_files() {
  local manifest_path local_file upstream_file baseline_hash local_hash category
  while IFS= read -r manifest_path; do
    [ -z "$manifest_path" ] && continue

    # CLAUDE.md lives at project root, not inside the platform dir.
    if [ "$manifest_path" = "CLAUDE.md" ]; then
      local_file="CLAUDE.md"
    elif [ "${manifest_path%%/*}" = "skills" ]; then
      local_file="$SKILLS_DIR/${manifest_path#skills/}"
    elif [ "$manifest_path" = "AGENTS.md.writ-block" ] || [ "$manifest_path" = "CLAUDE.md.writ-block" ] || [ "$manifest_path" = ".codex/config.toml.baseline" ]; then
      continue
    elif [ "${manifest_path%%/*}" = ".writ" ] || [ "${manifest_path%%/*}" = "scripts" ]; then
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

    # A file an earlier install shipped is stale when upstream no longer has
    # it, or when it is a script or doc a ship filter now rejects (e.g. the
    # ADR-029 dev-only helpers and the ADR-013 staging doc, which stay upstream
    # for eval.sh).
    if [ ! -f "$upstream_file" ] \
        || { [ "$category" = "scripts" ] && ! is_shippable_script "$(basename "$manifest_path")"; } \
        || { [ "$category" = ".writ" ] && ! is_shippable_writ_doc "$(basename "$manifest_path")"; }; then
      baseline_hash=$(manifest_hash_for "$manifest_path")
      local_hash=$(hash_file "$local_file")

      if [ "$local_hash" = "$baseline_hash" ]; then
        STALE_FILES="${STALE_FILES}${manifest_path}\n"
        STALE_COUNT=$((STALE_COUNT + 1))
      else
        # Locally modified: keep it in every category. write_copy_manifest
        # carries this old baseline forward (a stale path is not in the shipped
        # set, so nothing else records it), and the next update warns again
        # until the user deletes the file.
        echo "  ⚠️  Stale (no longer shipped, locally modified — kept): $manifest_path"
        STALE_KEPT_ENTRIES="${STALE_KEPT_ENTRIES}${baseline_hash}  ${manifest_path}\n"
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

echo "  Scripts:"
overlay_scan_flat_dir "$WRIT_SRC/scripts" "scripts" "scripts" "preview" "script"
TOTAL_NEW=$((TOTAL_NEW + _NEW))
TOTAL_UPDATED=$((TOTAL_UPDATED + _UPDATED))
TOTAL_PRESERVED=$((TOTAL_PRESERVED + _PRESERVED))
ALL_PRESERVED_FILES="${ALL_PRESERVED_FILES}${_PRESERVED_FILES}"

echo "  Writ docs:"
overlay_scan_flat_dir "$WRIT_SRC/.writ/docs" ".writ/docs" ".writ/docs" "preview" "doc"
TOTAL_NEW=$((TOTAL_NEW + _NEW))
TOTAL_UPDATED=$((TOTAL_UPDATED + _UPDATED))
TOTAL_PRESERVED=$((TOTAL_PRESERVED + _PRESERVED))
ALL_PRESERVED_FILES="${ALL_PRESERVED_FILES}${_PRESERVED_FILES}"

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
      elif [ "$rule_local" = "$rule_baseline" ] || { [ -z "$rule_baseline" ] && [ ! -f "$MANIFEST_FILE" ]; }; then
        RULE_ACTION="update"
        echo "    🔄 Update:    rules/writ.mdc"
      else
        RULE_ACTION="preserved"
        if [ -z "$rule_baseline" ]; then
          echo "    ⚡ Preserved: rules/writ.mdc (no baseline, assuming modified)"
        else
          echo "    ⚡ Preserved: rules/writ.mdc (local modifications)"
        fi
        TOTAL_PRESERVED=$((TOTAL_PRESERVED + 1))
        ALL_PRESERVED_FILES="${ALL_PRESERVED_FILES}    rules/writ.mdc\n"
      fi
    fi
  else
    RULE_ACTION="new"
    echo "    ✨ New:       rules/writ.mdc"
  fi
fi

# Cursor and Claude Code both install system-instructions.md in the platform dir.
if [ "$PLATFORM" = "cursor" ] || [ "$PLATFORM" = "claude" ]; then
  SYSINST_ACTION="unchanged"
  if [ -f "$PLATFORM_DIR/system-instructions.md" ]; then
    si_upstream=$(hash_file "$WRIT_SRC/system-instructions.md")
    si_local=$(hash_file "$PLATFORM_DIR/system-instructions.md")
    si_baseline=$(manifest_hash_for "system-instructions.md")

    if [ "$si_local" != "$si_upstream" ]; then
      if [ "$FORCE" = true ]; then
        SYSINST_ACTION="update"
        echo "    🔄 Update:    system-instructions.md (forced)"
      elif [ "$si_local" = "$si_baseline" ] || { [ -z "$si_baseline" ] && [ ! -f "$MANIFEST_FILE" ]; }; then
        SYSINST_ACTION="update"
        echo "    🔄 Update:    system-instructions.md"
      else
        SYSINST_ACTION="preserved"
        if [ -z "$si_baseline" ]; then
          echo "    ⚡ Preserved: system-instructions.md (no baseline, assuming modified)"
        else
          echo "    ⚡ Preserved: system-instructions.md (local modifications)"
        fi
        TOTAL_PRESERVED=$((TOTAL_PRESERVED + 1))
        ALL_PRESERVED_FILES="${ALL_PRESERVED_FILES}    system-instructions.md\n"
      fi
    fi
  elif [ -f "$WRIT_SRC/system-instructions.md" ]; then
    SYSINST_ACTION="new"
    echo "    ✨ New:       system-instructions.md"
  fi
fi

if [ "$PLATFORM" = "claude" ]; then
  echo "  CLAUDE.md:"
  merge_claude_md preview
  case "$CLAUDE_MD_ACTION" in
    preserved)
      TOTAL_PRESERVED=$((TOTAL_PRESERVED + 1))
      ALL_PRESERVED_FILES="${ALL_PRESERVED_FILES}    CLAUDE.md (Writ block)\n"
      ;;
  esac
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
  { [ "${SYSINST_ACTION:-unchanged}" = "update" ] || [ "${SYSINST_ACTION:-unchanged}" = "new" ]; } && ACTIONABLE=$((ACTIONABLE + 1))
  { [ "$CLAUDE_MD_ACTION" = "update" ] || [ "$CLAUDE_MD_ACTION" = "restore" ]; } && ACTIONABLE=$((ACTIONABLE + 1))
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
overlay_scan_flat_dir "$WRIT_SRC/scripts" "scripts" "scripts" "apply" "script"
overlay_scan_flat_dir "$WRIT_SRC/.writ/docs" ".writ/docs" ".writ/docs" "apply" "doc"
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
  if [ "$SYSINST_ACTION" = "update" ] || [ "$SYSINST_ACTION" = "new" ]; then
    cp "$WRIT_SRC/system-instructions.md" "$PLATFORM_DIR/"
    UPDATES=$((UPDATES + 1))
  fi
  if [ "$CLAUDE_MD_ACTION" = "update" ] || [ "$CLAUDE_MD_ACTION" = "restore" ]; then
    merge_claude_md apply
    UPDATES=$((UPDATES + 1))
  fi
elif [ "$PLATFORM" = "codex" ]; then
  if [ "$AGENTS_MD_ACTION" = "update" ] || [ "$AGENTS_MD_ACTION" = "restore" ]; then
    merge_agents_md apply
    UPDATES=$((UPDATES + 1))
  fi
fi

# Remove stale files. Skills live in $SKILLS_DIR, which on Codex is
# .agents/skills, not under $PLATFORM_DIR. A path is reported and counted only
# when it is gone after rm. One that rm could not remove keeps its manifest
# line, so the next update tries again. The loop reads a here-string, not a
# pipe, so the count and the kept lines reach this shell.
STALE_REMOVED=0
if [ "$STALE_COUNT" -gt 0 ]; then
  while IFS= read -r sf; do
    [ -n "$sf" ] || continue
    case "$sf" in
      CLAUDE.md)         stale_local="CLAUDE.md" ;;
      skills/*)          stale_local="$SKILLS_DIR/${sf#skills/}" ;;
      scripts/*|.writ/*) stale_local="$sf" ;;
      *)                 stale_local="$PLATFORM_DIR/$sf" ;;
    esac
    rm -f "$stale_local" || true
    if [ -e "$stale_local" ] || [ -L "$stale_local" ]; then
      STALE_KEPT_ENTRIES="${STALE_KEPT_ENTRIES}$(manifest_hash_for "$sf")  ${sf}\n"
      continue
    fi
    echo "  🗑  Removed: $sf"
    STALE_REMOVED=$((STALE_REMOVED + 1))
  done <<< "$(printf "%b" "$STALE_FILES")"
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
  f=""; base=""
  for f in scripts/*.py scripts/*.sh scripts/jev-thresholds.json; do
    [ -f "$f" ] || continue
    base=$(basename "$f")
    is_shippable_script "$base" && git add "$f" 2>/dev/null || true
  done
  git add .writ/docs/*.md 2>/dev/null || true
  git add "$PLATFORM_DIR/commands/" "$PLATFORM_DIR/agents/" "$MANIFEST_FILE" 2>/dev/null || true
  [ -d "$SKILLS_DIR" ] && git add "$SKILLS_DIR/" 2>/dev/null || true
  if [ "$PLATFORM" = "cursor" ]; then
    git add "$PLATFORM_DIR/rules/writ.mdc" "$PLATFORM_DIR/system-instructions.md" 2>/dev/null || true
  elif [ "$PLATFORM" = "claude" ]; then
    git add "CLAUDE.md" 2>/dev/null || true
    git add "$PLATFORM_DIR/system-instructions.md" 2>/dev/null || true
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

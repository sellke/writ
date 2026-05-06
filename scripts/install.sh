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
#   --platform     Target platform: cursor (default), claude, or codex

set -euo pipefail

WRIT_REPO="https://github.com/sellke/writ.git"

DRY_RUN=false
NO_COMMIT=false
FORCE=false
PLATFORM="cursor"
WRIT_CODEX_CONFIG_BASELINE_HASH=""

while [ $# -gt 0 ]; do
  case $1 in
    --dry-run)    DRY_RUN=true ;;
    --no-commit)  NO_COMMIT=true ;;
    --force)      FORCE=true ;;
    --platform)
      shift
      PLATFORM="${1:-}"
      if [ "$PLATFORM" != "cursor" ] && [ "$PLATFORM" != "claude" ] && [ "$PLATFORM" != "codex" ]; then
        echo "❌ Unknown platform: $PLATFORM"
        echo "   Supported: cursor, claude, codex"
        exit 1
      fi
      ;;
    --help|-h)
      echo "Usage: bash install.sh [--dry-run] [--no-commit] [--force] [--platform cursor|claude|codex]"
      echo ""
      echo "Installs Writ commands, agents, and rules into your project."
      echo "Run from your project root."
      echo ""
      echo "Platforms:"
      echo "  cursor (default)  Install into .cursor/ for Cursor IDE"
      echo "  claude            Install into .claude/ for Claude Code CLI"
      echo "  codex             Install into .codex/ for Codex CLI (AGENTS.md + .agents/skills/)"
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

# <<< writ-merge-bundled-begin (used by scripts/tests/test_merge_agents_md.sh — keep synced) >>>
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
  local staging
  staging=$(mktemp)
  local start_line end_line
  read -r start_line end_line <<<"$(awk '{
      line=$0
      sub(/\r$/, "", line)
      if (line == "<!-- writ:start -->") { printf "%d ", NR; found_s=1 }
      if (line == "<!-- writ:end -->") { print NR; exit }
    }' "$file")"
  if [ -z "${start_line:-}" ] || [ -z "${end_line:-}" ]; then
    rm -f "$staging"
    return 1
  fi
  if [ "$start_line" -ge "$end_line" ]; then
    rm -f "$staging"
    return 2
  fi
  if [ "${start_line:-0}" -le 0 ]; then
    rm -f "$staging"
    return 2
  fi
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

# merge_agents_md — Codex ONLY. Integrates codex/AGENTS.md.template into AGENTS.md
# Globals: WRIT_SRC, MANIFEST_FILE, FORCE, CODEX_MERGE_PREVIEW (optional)
merge_agents_md() {
  local op="${1:-apply}" # preview | apply
  local template="$WRIT_SRC/codex/AGENTS.md.template"
  if [ ! -f "$template" ]; then
    echo "❌ Missing $template — cannot integrate AGENTS.md for Codex."
    return 12
  fi
  AGENTS_MERGE_NOTE=""
  local upstream_inner
  upstream_inner=$(cat "$template")
  local upstream_hash
  upstream_hash=$(hash_file "$template")

  local agents_md="AGENTS.md"
  if [ "$op" = "preview" ]; then
    if [ ! -f "$agents_md" ]; then
      AGENTS_MERGE_NOTE="Would create AGENTS.md with Writ block (no prior file)."
      printf '%s\n' "$AGENTS_MERGE_NOTE"
      return 0
    fi
    local cnt
    cnt=$(writ_block_marker_counts "$agents_md")
    local start_cnt end_cnt
    read -r start_cnt end_cnt <<<"$cnt"
    if [ "${start_cnt:-0}" -eq 0 ] && [ "${end_cnt:-0}" -eq 0 ]; then
      AGENTS_MERGE_NOTE="Would append Writ block to existing AGENTS.md (no markers found)."
      printf '%s\n' "$AGENTS_MERGE_NOTE"
      return 0
    fi
    if [ "${start_cnt:-0}" -ne 1 ] || [ "${end_cnt:-0}" -ne 1 ]; then
      AGENTS_MERGE_NOTE="Writ block error: malformed markers (expected exactly one start and end marker)."
      printf '%s\n' "$AGENTS_MERGE_NOTE"
      return 0
    fi
    local start_line end_line
    read -r start_line end_line <<<"$(awk '{
        line=$0
        sub(/\r$/, "", line)
        if (line == "<!-- writ:start -->") printf "%d ", NR
        if (line == "<!-- writ:end -->") print NR
      }' "$agents_md")"
    if [ "${start_line:-0}" -ge "${end_line:-0}" ]; then
      AGENTS_MERGE_NOTE="Writ block error: malformed marker order."
      printf '%s\n' "$AGENTS_MERGE_NOTE"
      return 0
    fi
    local inner_hash=""
    inner_hash=""
    if ! inner_hash="$(writ_compute_writ_block_inner_hash "$agents_md")"; then
      AGENTS_MERGE_NOTE="Writ block error: malformed markers (inner parse)."
      printf '%s\n' "$AGENTS_MERGE_NOTE"
      return 0
    fi
    local baseline_hash
    baseline_hash=$(manifest_hash_for "AGENTS.md.writ-block")
    if [ "$FORCE" = true ]; then
      AGENTS_MERGE_NOTE="Would replace marker-bounded Writ block (--force)."
      printf '%s\n' "$AGENTS_MERGE_NOTE"
      return 0
    fi
    if [ "$inner_hash" = "$upstream_hash" ]; then
      AGENTS_MERGE_NOTE="Writ block already matches upstream template (unchanged)."
      printf '%s\n' "$AGENTS_MERGE_NOTE"
      return 0
    fi
    if [ -n "$baseline_hash" ] && [ "$inner_hash" = "$baseline_hash" ]; then
      AGENTS_MERGE_NOTE="Would update Writ block (matches manifest baseline → safe overwrite)."
      printf '%s\n' "$AGENTS_MERGE_NOTE"
      return 0
    fi
    AGENTS_MERGE_NOTE="Would preserve Writ block (local modifications detected)."
    printf '%s\n' "$AGENTS_MERGE_NOTE"
    return 0
  fi

  local tmp_new
  tmp_new=$(mktemp)

  if [ ! -f "$agents_md" ]; then
    printf '%s\n' '<!-- writ:start -->' > "$tmp_new"
    printf '%s\n' "$upstream_inner" >> "$tmp_new"
    printf '%s\n' '<!-- writ:end -->' >> "$tmp_new"
    mv "$tmp_new" "$agents_md"
    AGENTS_MERGE_NOTE="AGENTS.md: Writ block created"
    return 0
  fi

  local cnt
  cnt=$(writ_block_marker_counts "$agents_md")
  local start_cnt end_cnt
  read -r start_cnt end_cnt <<<"$cnt"
  if [ "${start_cnt:-0}" -eq 0 ] && [ "${end_cnt:-0}" -eq 0 ]; then
    cat "$agents_md" >> "$tmp_new"
    if ! writ_file_ends_with_newline "$agents_md"; then
      printf '\n' >> "$tmp_new"
    fi
    printf '%s\n' '<!-- writ:start -->' >> "$tmp_new"
    printf '%s\n' "$upstream_inner" >> "$tmp_new"
    printf '%s\n' '<!-- writ:end -->' >> "$tmp_new"
    mv "$tmp_new" "$agents_md"
    AGENTS_MERGE_NOTE="AGENTS.md: Writ block appended (existing content preserved)"
    return 0
  fi

  if [ "${start_cnt:-0}" -ne 1 ] || [ "${end_cnt:-0}" -ne 1 ]; then
    rm -f "$tmp_new"
    AGENTS_MERGE_NOTE="AGENTS.md: Writ block error: malformed markers"
    printf '%s\n' "❌ $AGENTS_MERGE_NOTE (expected exactly one <!-- writ:start --> and one <!-- writ:end -->)."
    return 13
  fi

  local start_line end_line
  read -r start_line end_line <<<"$(awk '{
      line=$0
      sub(/\r$/, "", line)
      if (line == "<!-- writ:start -->") printf "%d ", NR
      if (line == "<!-- writ:end -->") print NR
    }' "$agents_md")"

  if [ -z "${start_line:-}" ] || [ -z "${end_line:-}" ] || [ "${start_line:-0}" -ge "${end_line:-0}" ]; then
    rm -f "$tmp_new"
    AGENTS_MERGE_NOTE="AGENTS.md: Writ block error: malformed markers"
    printf '%s\n' "❌ $AGENTS_MERGE_NOTE (invalid marker order)."
    return 13
  fi

  local inner_hash=""
  if ! inner_hash="$(writ_compute_writ_block_inner_hash "$agents_md")"; then
    rm -f "$tmp_new"
    AGENTS_MERGE_NOTE="AGENTS.md: Writ block error: malformed markers"
    printf '%s\n' "❌ $AGENTS_MERGE_NOTE (inner block parse failed)."
    return 13
  fi

  local baseline_hash
  baseline_hash=$(manifest_hash_for "AGENTS.md.writ-block")

  if [ "$FORCE" = true ]; then
    writ_rewrite_agents_md_with_inner "$agents_md" "$upstream_inner"
    rm -f "$tmp_new"
    AGENTS_MERGE_NOTE="AGENTS.md: Writ block updated (--force)"
    return 0
  fi

  if [ "$inner_hash" = "$upstream_hash" ]; then
    rm -f "$tmp_new"
    AGENTS_MERGE_NOTE="AGENTS.md: Writ block preserved (already current)"
    return 0
  fi

  if [ -n "$baseline_hash" ] && [ "$inner_hash" = "$baseline_hash" ]; then
    writ_rewrite_agents_md_with_inner "$agents_md" "$upstream_inner"
    rm -f "$tmp_new"
    AGENTS_MERGE_NOTE="AGENTS.md: Writ block updated"
    return 0
  fi

  rm -f "$tmp_new"
  AGENTS_MERGE_NOTE="AGENTS.md: Writ block preserved (local modifications)"
  printf '%s\n' "⚡ $AGENTS_MERGE_NOTE — re-run with --force to overwrite the Writ block."
  return 0
}
# <<< writ-merge-bundled-end >>>

# seed_codex_config — install-once copy of codex/config.toml.template.
# Globals: WRIT_SRC, MANIFEST_FILE, PLATFORM_DIR
seed_codex_config() {
  local op="${1:-apply}" # preview | apply
  local template="$WRIT_SRC/codex/config.toml.template"
  local dest=".codex/config.toml"
  SEED_CODEX_CONFIG_NOTE=""
  if [ ! -f "$template" ]; then
    echo "❌ Missing $template — cannot seed Codex config."
    return 14
  fi
  if [ "$op" = "preview" ]; then
    if [ -f "$dest" ]; then
      SEED_CODEX_CONFIG_NOTE="Would skip .codex/config.toml (already exists; install-once)."
    else
      SEED_CODEX_CONFIG_NOTE="Would seed .codex/config.toml from template (first install)."
    fi
    printf '%s\n' "$SEED_CODEX_CONFIG_NOTE"
    return 0
  fi
  if [ -f "$dest" ]; then
    WRIT_CODEX_CONFIG_BASELINE_HASH="$(manifest_hash_for ".codex/config.toml.baseline")"
    SEED_CODEX_CONFIG_NOTE="⚡ Preserved: .codex/config.toml (install-once)"
    printf '%s\n' "$SEED_CODEX_CONFIG_NOTE"
    return 0
  fi
  mkdir -p "$(dirname "$dest")"
  cp "$template" "$dest"
  WRIT_CODEX_CONFIG_BASELINE_HASH="$(hash_file "$template")"
  SEED_CODEX_CONFIG_NOTE="✨ Seeded: .codex/config.toml"
  printf '%s\n' "$SEED_CODEX_CONFIG_NOTE"
  return 0
}

writ_warn_agents_md_size() {
  local max_bytes=32768
  [ -f "AGENTS.md" ] || return 0
  local sz
  sz=$(wc -c < "AGENTS.md" | tr -d ' ')
  if [ "${sz:-0}" -gt "$max_bytes" ]; then
    local kb=$(( (sz + 1023) / 1024 ))
    printf '%s\n' "⚠️  AGENTS.md is ${kb} KiB, exceeds default Codex cap (32 KiB). Configure project_doc_max_bytes or split via AGENTS.override.md." >&2
  fi
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
    local iw=""
    if [ -f "AGENTS.md" ] && iw="$(writ_compute_writ_block_inner_hash "AGENTS.md")"; then
      echo "$iw  AGENTS.md.writ-block" >> "$target"
    fi
    if [ -n "${WRIT_CODEX_CONFIG_BASELINE_HASH:-}" ]; then
      echo "$WRIT_CODEX_CONFIG_BASELINE_HASH  .codex/config.toml.baseline" >> "$target"
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
for f in "$WRIT_SRC/$AGENTS_SRC/"$AGENT_FILE_GLOB; do [ -f "$f" ] && AGENT_COUNT=$((AGENT_COUNT + 1)); done
SKILL_COUNT=0
if [ -d "$WRIT_SRC/skills" ]; then
  for d in "$WRIT_SRC/skills"/*/; do [ -d "$d" ] && [ -f "${d}SKILL.md" ] && SKILL_COUNT=$((SKILL_COUNT + 1)); done
fi

if [ "$PLATFORM" = "codex" ] && [ "$AGENT_COUNT" -eq 0 ]; then
  printf '%s\n' "⚠️  codex/agents/ source missing — agent install skipped" >&2
fi

echo "  📋 Commands:  $CMD_COUNT"
echo "  🤖 Agents:    $AGENT_COUNT"
[ "$SKILL_COUNT" -gt 0 ] && echo "  📜 Skills:    $SKILL_COUNT"
if [ "$PLATFORM" = "cursor" ]; then
  echo "  📜 Rules:     1 (writ.mdc)"
  echo "  📖 System:    1 (system-instructions.md)"
elif [ "$PLATFORM" = "claude" ]; then
  echo "  📖 Root:      1 (CLAUDE.md)"
elif [ "$PLATFORM" = "codex" ]; then
  echo "  📄 AGENTS.md Writ block (.agents/skills/ for AgentSkills)"
  echo "  🧩 Codex cfg: install-once .codex/config.toml when absent"
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
  local src_dir="$1" local_dir="$2" label="$3" mode="$4" pattern="${5:-*.md}"
  _NEW=0; _UPDATED=0; _PRESERVED=0; _UNCHANGED=0

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

# Skills overlay — folder-aware, SKILL.md hash-tracked, sidecar files install-once.
# Mirrors overlay_scan semantics for SKILL.md; never overwrites sidecar files after first install.
overlay_scan_skills() {
  local src_dir="$1" local_dir="$2" mode="$3"
  _NEW=0; _UPDATED=0; _PRESERVED=0; _UNCHANGED=0

  local skill_folder skill_name src_skill local_skill rel_path upstream_hash local_hash baseline_hash
  local sidecar sidecar_name local_sidecar
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
        # Sidecar files copied on first install only
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
      if [ "$mode" = "preview" ]; then echo "    ⚡ Preserved: $rel_path (no baseline, assuming modified)"; fi
    elif [ "$local_hash" = "$baseline_hash" ]; then
      _UPDATED=$((_UPDATED + 1))
      if [ "$mode" = "preview" ]; then echo "    🔄 Update:    $rel_path"; fi
      if [ "$mode" = "apply" ];   then cp "$src_skill" "$local_skill"; fi
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
    echo "  Would replace symlinks with copies ($CMD_COUNT commands, $AGENT_COUNT agents$([ "$SKILL_COUNT" -gt 0 ] && echo ", $SKILL_COUNT skills"))."
  else
    echo "  Commands:"
    overlay_scan "$WRIT_SRC/commands" "$PLATFORM_DIR/commands" "commands" "preview"
    echo ""
    echo "  Agents:"
    overlay_scan "$WRIT_SRC/$AGENTS_SRC" "$PLATFORM_DIR/agents" "agents" "preview" "$AGENT_FILE_GLOB"
    echo ""
    if [ -d "$WRIT_SRC/skills" ] && [ "$SKILL_COUNT" -gt 0 ]; then
      echo "  Skills:"
      overlay_scan_skills "$WRIT_SRC/skills" "$SKILLS_DIR" "preview"
      echo ""
    fi
    if [ "$PLATFORM" = "cursor" ]; then
      echo "  Rules:   writ.mdc → always updated"
      echo "  System:  system-instructions.md → always updated"
    elif [ "$PLATFORM" = "claude" ]; then
      echo "  Root:    CLAUDE.md → always updated"
    elif [ "$PLATFORM" = "codex" ]; then
      echo "  AGENTS.md integration plan:"
      merge_agents_md preview
      echo "  Codex config seed plan:"
      seed_codex_config preview
    fi
  fi
  echo ""
  echo "💡 To reset a file to core: delete the local copy and re-run install."
  echo "💡 To force overwrite all: install.sh --force"
  if [ "$PLATFORM" = "codex" ] && [ "$AGENT_COUNT" -eq 0 ]; then
    exit 1
  fi
  exit 0
fi

# --- Install ---

echo "Installing..."

# Remove symlinks if converting from a linked installation
if [ "$EXISTING_MODE" = "link" ]; then
  echo "  Removing symlinks..."
  for f in "$PLATFORM_DIR"/commands/*.md; do
    [ -L "$f" ] && rm -f "$f"
  done
  for f in "$PLATFORM_DIR"/agents/*.md "$PLATFORM_DIR"/agents/*.toml; do
    [ -L "$f" ] && rm -f "$f"
  done
  for f in "$PLATFORM_DIR/commands" "$PLATFORM_DIR/agents"; do
    [ -L "$f" ] && rm -f "$f"
  done
  if [ -d "$SKILLS_DIR" ] || [ -L "$SKILLS_DIR" ]; then
    for skill_folder in "$SKILLS_DIR"/*/; do
      [ -L "${skill_folder%/}" ] && rm -f "${skill_folder%/}"
      [ -L "${skill_folder}SKILL.md" ] && rm -f "${skill_folder}SKILL.md"
    done
    [ -L "$SKILLS_DIR" ] && rm -f "$SKILLS_DIR"
  fi
  if [ "$PLATFORM" = "cursor" ]; then
    for f in "$PLATFORM_DIR/rules/writ.mdc" "$PLATFORM_DIR/system-instructions.md"; do
      [ -L "$f" ] && rm -f "$f"
    done
  elif [ "$PLATFORM" = "claude" ]; then
    [ -L "CLAUDE.md" ] && rm -f "CLAUDE.md"
  fi
fi

mkdir -p "$PLATFORM_DIR/commands" "$PLATFORM_DIR/agents"
[ -d "$WRIT_SRC/skills" ] && mkdir -p "$SKILLS_DIR"
[ "$PLATFORM" = "cursor" ] && mkdir -p "$PLATFORM_DIR/rules"

if [ "$PLATFORM" = "codex" ]; then
  if [ -d "$WRIT_SRC/skills" ] && [ "$SKILL_COUNT" -gt 0 ]; then
    STEP_TOTAL=6
  else
    STEP_TOTAL=5
  fi
elif [ -d "$WRIT_SRC/skills" ] && [ "$SKILL_COUNT" -gt 0 ]; then
  STEP_TOTAL=6
else
  STEP_TOTAL=5
fi
STEP=0

STEP=$((STEP + 1))
echo "  [$STEP/$STEP_TOTAL] Commands..."
overlay_scan "$WRIT_SRC/commands" "$PLATFORM_DIR/commands" "commands" "apply"
CMD_NEW=$_NEW; CMD_UPDATED=$_UPDATED; CMD_PRESERVED=$_PRESERVED

STEP=$((STEP + 1))
echo "  [$STEP/$STEP_TOTAL] Agents..."
overlay_scan "$WRIT_SRC/$AGENTS_SRC" "$PLATFORM_DIR/agents" "agents" "apply" "$AGENT_FILE_GLOB"
AGENT_NEW=$_NEW; AGENT_UPDATED=$_UPDATED; AGENT_PRESERVED=$_PRESERVED

SKILL_NEW=0; SKILL_UPDATED=0; SKILL_PRESERVED=0
if [ -d "$WRIT_SRC/skills" ] && [ "$SKILL_COUNT" -gt 0 ]; then
  STEP=$((STEP + 1))
  echo "  [$STEP/$STEP_TOTAL] Skills..."
  overlay_scan_skills "$WRIT_SRC/skills" "$SKILLS_DIR" "apply"
  SKILL_NEW=$_NEW; SKILL_UPDATED=$_UPDATED; SKILL_PRESERVED=$_PRESERVED
fi

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
elif [ "$PLATFORM" = "codex" ]; then
  echo "  [$STEP/$STEP_TOTAL] AGENTS.md integration..."
  merge_agents_md apply
  STEP=$((STEP + 1))
  echo "  [$STEP/$STEP_TOTAL] Codex CLI config..."
  seed_codex_config apply
  writ_warn_agents_md_size
fi

STEP=$((STEP + 1))
echo "  [$STEP/$STEP_TOTAL] Writing manifest..."
write_copy_manifest "$VERSION" "$MANIFEST_FILE"

init_writ_workspace

# --- Summary ---

echo ""

if [ "$PLATFORM" = "codex" ] && [ "${AGENT_COUNT:-0}" -eq 0 ]; then
  echo "❌ Codex agent sources were missing; install incomplete."
  exit 1
fi

echo "✅ Writ installed for $PLATFORM_LABEL! (version: $VERSION)"

TOTAL_NEW=$((CMD_NEW + AGENT_NEW + SKILL_NEW))
TOTAL_UPDATED=$((CMD_UPDATED + AGENT_UPDATED + SKILL_UPDATED))
TOTAL_PRESERVED=$((CMD_PRESERVED + AGENT_PRESERVED + SKILL_PRESERVED))

if [ "$TOTAL_NEW" -gt 0 ] || [ "$TOTAL_UPDATED" -gt 0 ] || [ "$TOTAL_PRESERVED" -gt 0 ]; then
  echo ""
  echo "  📋 Summary:"
  [ "$TOTAL_NEW" -gt 0 ]       && echo "     $TOTAL_NEW new file(s) installed"
  [ "$TOTAL_UPDATED" -gt 0 ]   && echo "     $TOTAL_UPDATED file(s) updated"
  [ "$TOTAL_PRESERVED" -gt 0 ] && echo "     $TOTAL_PRESERVED file(s) preserved (local modifications kept)"
  if [ "$SKILL_NEW" -gt 0 ] || [ "$SKILL_UPDATED" -gt 0 ] || [ "$SKILL_PRESERVED" -gt 0 ]; then
    echo "     Skills: $SKILL_NEW new, $SKILL_UPDATED updated, $SKILL_PRESERVED preserved"
  fi
  if [ "$TOTAL_PRESERVED" -gt 0 ]; then
    echo ""
    echo "  💡 To reset a file to core: delete it and re-run install."
    echo "  💡 To force overwrite all: install.sh --force"
  fi
fi

if [ "$PLATFORM" = "codex" ]; then
  echo ""
  [ -n "${AGENTS_MERGE_NOTE:-}" ] && echo "  $AGENTS_MERGE_NOTE"
  [ -n "${SEED_CODEX_CONFIG_NOTE:-}" ] && echo "  $SEED_CODEX_CONFIG_NOTE"
fi

# --- Scoped git commit ---

if [ "$NO_COMMIT" = false ] && command -v git &>/dev/null && [ -d .git ]; then
  git add "$PLATFORM_DIR/commands/" "$PLATFORM_DIR/agents/" 2>/dev/null || true
  [ -d "$SKILLS_DIR" ] && git add "$SKILLS_DIR/" 2>/dev/null || true
  if [ "$PLATFORM" = "cursor" ]; then
    git add "$PLATFORM_DIR/rules/writ.mdc" "$PLATFORM_DIR/system-instructions.md" 2>/dev/null || true
  elif [ "$PLATFORM" = "claude" ]; then
    git add "CLAUDE.md" 2>/dev/null || true
  elif [ "$PLATFORM" = "codex" ]; then
    git add "AGENTS.md" ".codex/config.toml" 2>/dev/null || true
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
elif [ "$PLATFORM" = "codex" ]; then
  echo "  In Codex CLI, restart sessions to reload AGENTS.md — try /create-spec, /implement-story"
fi
echo ""
echo "⚡ So it is written. So it shall be built."

#!/bin/bash
# Writ Uninstaller — removes Writ commands, agents, rules, and manifest
# Run from your project root: bash <(curl -s https://raw.githubusercontent.com/sellke/writ/main/scripts/uninstall.sh)
#
# Removes platform files only. The .writ/ directory (specs, docs, ADRs) is preserved.
#
# Flags:
#   --dry-run      Preview changes without applying
#   --no-commit    Don't auto-commit after removal
#   --platform     Target platform: cursor (default), claude, or codex
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
      if [ "$PLATFORM" != "cursor" ] && [ "$PLATFORM" != "claude" ] && [ "$PLATFORM" != "codex" ]; then
        echo "❌ Unknown platform: $PLATFORM"
        echo "   Supported: cursor, claude, codex"
        exit 1
      fi
      ;;
    --help|-h)
      echo "Usage: bash uninstall.sh [--dry-run] [--no-commit] [--platform cursor|claude|codex] [--include-writ]"
      echo ""
      echo "Removes Writ commands, agents, rules, and manifest from your project."
      echo "Run from your project root."
      echo ""
      echo "Platforms:"
      echo "  cursor (default)  Remove from .cursor/"
      echo "  claude            Remove from .claude/"
      echo "  codex             Remove from .codex/, .agents/skills/, and AGENTS.md Writ block"
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
  HAS_CODEX=false
  [ -f ".cursor/.writ-manifest" ] && HAS_CURSOR=true
  [ -f ".claude/.writ-manifest" ] && HAS_CLAUDE=true
  [ -f ".codex/.writ-manifest" ] && HAS_CODEX=true

  INSTALL_COUNT=0
  [ "$HAS_CURSOR" = true ] && INSTALL_COUNT=$((INSTALL_COUNT + 1))
  [ "$HAS_CLAUDE" = true ] && INSTALL_COUNT=$((INSTALL_COUNT + 1))
  [ "$HAS_CODEX" = true ] && INSTALL_COUNT=$((INSTALL_COUNT + 1))

  if [ "$INSTALL_COUNT" -gt 1 ]; then
    echo "❌ Multiple Writ installations detected."
    echo "   Specify which to remove: --platform cursor, --platform claude, or --platform codex"
    echo "   Run once per platform to remove multiple installations."
    exit 1
  elif [ "$HAS_CURSOR" = true ]; then
    PLATFORM="cursor"
  elif [ "$HAS_CLAUDE" = true ]; then
    PLATFORM="claude"
  elif [ "$HAS_CODEX" = true ]; then
    PLATFORM="codex"
  else
    # No manifest — check for Writ files anyway
    if [ -d ".cursor/commands" ] && ls .cursor/commands/*.md &>/dev/null; then
      PLATFORM="cursor"
      echo "  ⚠️  No manifest found but Writ files detected in .cursor/"
    elif [ -d ".claude/commands" ] && ls .claude/commands/*.md &>/dev/null; then
      PLATFORM="claude"
      echo "  ⚠️  No manifest found but Writ files detected in .claude/"
    elif [ -d ".codex/commands" ] && ls .codex/commands/*.md &>/dev/null; then
      PLATFORM="codex"
      echo "  ⚠️  No manifest found but Writ files detected in .codex/"
    else
      echo "❌ Writ doesn't appear to be installed in this project."
      echo "   No manifest or Writ files found in .cursor/, .claude/, or .codex/"
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
  SKILLS_DIR=".cursor/skills"
  AGENT_FILE_GLOB="*.md"
elif [ "$PLATFORM" = "claude" ]; then
  PLATFORM_DIR=".claude"
  PLATFORM_LABEL="Claude Code"
  SKILLS_DIR=".claude/skills"
  AGENT_FILE_GLOB="*.md"
elif [ "$PLATFORM" = "codex" ]; then
  PLATFORM_DIR=".codex"
  PLATFORM_LABEL="Codex CLI"
  SKILLS_DIR=".agents/skills"
  AGENT_FILE_GLOB="*.toml"
fi

echo "⚡ Writ Uninstaller ($PLATFORM_LABEL)"
echo "==================="
echo ""

# <<< writ-remove-agents-md-bundled-begin (used by scripts/tests/test_remove_agents_md_block.sh — keep synced) >>>
writ_agents_md_marker_counts() {
  local file="$1"
  awk '{
      line=$0
      sub(/\r$/, "", line)
      if (line == "<!-- writ:start -->") starts++
      if (line == "<!-- writ:end -->") ends++
    }
    END { print starts + 0, ends + 0 }' "$file"
}

remove_agents_md_block() {
  local file="${1:-AGENTS.md}"
  REMOVE_AGENTS_MD_NOTE=""

  if [ ! -f "$file" ]; then
    REMOVE_AGENTS_MD_NOTE="✓ AGENTS.md (no file present)"
    return 0
  fi

  local counts start_count end_count
  counts=$(writ_agents_md_marker_counts "$file")
  read -r start_count end_count <<<"$counts"

  if [ "${start_count:-0}" -eq 0 ] && [ "${end_count:-0}" -eq 0 ]; then
    REMOVE_AGENTS_MD_NOTE="✓ AGENTS.md (no Writ block present)"
    return 0
  fi

  if [ "${start_count:-0}" -ne 1 ] || [ "${end_count:-0}" -ne 1 ]; then
    REMOVE_AGENTS_MD_NOTE="AGENTS.md block error: malformed markers"
    printf '%s\n' "❌ $REMOVE_AGENTS_MD_NOTE (expected exactly one <!-- writ:start --> and one <!-- writ:end -->)." >&2
    return 13
  fi

  local start_line end_line
  read -r start_line end_line <<<"$(awk '{
      line=$0
      sub(/\r$/, "", line)
      if (line == "<!-- writ:start -->") printf "%d ", NR
      if (line == "<!-- writ:end -->") print NR
    }' "$file")"

  if [ -z "${start_line:-}" ] || [ -z "${end_line:-}" ] || [ "${start_line:-0}" -ge "${end_line:-0}" ]; then
    REMOVE_AGENTS_MD_NOTE="AGENTS.md block error: malformed markers"
    printf '%s\n' "❌ $REMOVE_AGENTS_MD_NOTE (invalid marker order)." >&2
    return 13
  fi

  local tmp
  tmp=$(mktemp)
  awk -v start="$start_line" -v end="$end_line" '
    NR < start { before[++bc] = $0; next }
    NR > end { after[++ac] = $0; next }
    END {
      while (bc > 0 && before[bc] ~ /^[[:space:]]*$/) bc--
      lead = 1
      while (lead <= ac && after[lead] ~ /^[[:space:]]*$/) lead++

      printed = 0
      for (i = 1; i <= bc; i++) {
        print before[i]
        printed = 1
      }
      if (printed && lead <= ac) print ""
      for (i = lead; i <= ac; i++) {
        print after[i]
        printed = 1
      }
    }' "$file" >"$tmp"

  if ! awk 'NF { found=1 } END { exit found ? 0 : 1 }' "$tmp"; then
    rm -f "$tmp" "$file"
    REMOVE_AGENTS_MD_NOTE="🗑  Removed: AGENTS.md (empty after Writ block removal)"
    return 0
  fi

  mv "$tmp" "$file"
  REMOVE_AGENTS_MD_NOTE="🗑  Removed: AGENTS.md Writ block"
  return 0
}
# <<< writ-remove-agents-md-bundled-end >>>

manifest_files() {
  [ -f "$PLATFORM_DIR/.writ-manifest" ] && grep -v '^#' "$PLATFORM_DIR/.writ-manifest" | grep -v '^$' | awk '{print $2}' || true
}

# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------

CMD_COUNT=0
AGENT_COUNT=0
SKILL_COUNT=0
EXTRA_FILES=()
CODEX_EXTRA_COUNT=0
CODEX_EXTRA_DESC=""

for f in "$PLATFORM_DIR"/commands/*.md; do
  [ -f "$f" ] && CMD_COUNT=$((CMD_COUNT + 1))
done

for f in "$PLATFORM_DIR"/agents/$AGENT_FILE_GLOB; do
  [ -f "$f" ] && AGENT_COUNT=$((AGENT_COUNT + 1))
done

if [ -d "$SKILLS_DIR" ]; then
  while IFS= read -r manifest_path; do
    case "$manifest_path" in
      skills/*/SKILL.md)
        local_skill="$SKILLS_DIR/${manifest_path#skills/}"
        [ -f "$local_skill" ] && SKILL_COUNT=$((SKILL_COUNT + 1))
        ;;
    esac
  done <<< "$(manifest_files)"
fi

if [ "$PLATFORM" = "cursor" ]; then
  [ -f "$PLATFORM_DIR/rules/writ.mdc" ] && EXTRA_FILES+=("$PLATFORM_DIR/rules/writ.mdc")
  [ -f "$PLATFORM_DIR/system-instructions.md" ] && EXTRA_FILES+=("$PLATFORM_DIR/system-instructions.md")
elif [ "$PLATFORM" = "claude" ]; then
  [ -f "CLAUDE.md" ] && EXTRA_FILES+=("CLAUDE.md")
elif [ "$PLATFORM" = "codex" ]; then
  if [ -f "AGENTS.md" ]; then
    CODEX_EXTRA_COUNT=$((CODEX_EXTRA_COUNT + 1))
    CODEX_EXTRA_DESC="${CODEX_EXTRA_DESC}AGENTS.md Writ block "
  fi
  if [ -f "$PLATFORM_DIR/config.toml" ]; then
    CODEX_EXTRA_COUNT=$((CODEX_EXTRA_COUNT + 1))
    CODEX_EXTRA_DESC="${CODEX_EXTRA_DESC}$PLATFORM_DIR/config.toml (prompt) "
  fi
fi

HAS_MANIFEST=false
[ -f "$PLATFORM_DIR/.writ-manifest" ] && HAS_MANIFEST=true

echo "  Files to remove:"
echo "    📋 Commands:  $CMD_COUNT"
echo "    🤖 Agents:    $AGENT_COUNT"
echo "    📜 Skills:    $SKILL_COUNT"
echo "    📄 Extras:    $((${#EXTRA_FILES[@]} + CODEX_EXTRA_COUNT)) (${EXTRA_FILES[*]:-${CODEX_EXTRA_DESC:-none}})"
[ "$HAS_MANIFEST" = true ] && echo "    📌 Manifest:  1"
echo ""

if [ "$INCLUDE_WRIT" = true ] && [ -d ".writ" ]; then
  WRIT_FILE_COUNT=$(find .writ -type f 2>/dev/null | wc -l | tr -d ' ')
  echo "  ⚠️  --include-writ: Also removing .writ/ ($WRIT_FILE_COUNT files)"
  echo "     This includes specs, docs, ADRs, and all work artifacts."
  echo ""
fi

TOTAL=$((CMD_COUNT + AGENT_COUNT + SKILL_COUNT + ${#EXTRA_FILES[@]} + CODEX_EXTRA_COUNT))
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
  for f in "$PLATFORM_DIR"/agents/$AGENT_FILE_GLOB; do
    [ -f "$f" ] && echo "  🗑  $f"
  done
  if [ "$SKILL_COUNT" -gt 0 ]; then
    while IFS= read -r manifest_path; do
      case "$manifest_path" in
        skills/*/SKILL.md)
          local_skill="$SKILLS_DIR/${manifest_path#skills/}"
          [ -f "$local_skill" ] && echo "  🗑  $local_skill"
          ;;
      esac
    done <<< "$(manifest_files)"
  fi
  for f in ${EXTRA_FILES[@]+"${EXTRA_FILES[@]}"}; do
    echo "  🗑  $f"
  done
  if [ "$PLATFORM" = "codex" ]; then
    [ -f "AGENTS.md" ] && echo "  🗑  AGENTS.md Writ block"
    [ -f "$PLATFORM_DIR/config.toml" ] && echo "  Would prompt: remove .codex/config.toml?"
  fi
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

for f in "$PLATFORM_DIR"/agents/$AGENT_FILE_GLOB; do
  if [ -f "$f" ] || [ -L "$f" ]; then
    rm -f "$f"
    REMOVED=$((REMOVED + 1))
  fi
done

# Remove agents dir if empty
rmdir "$PLATFORM_DIR/agents" 2>/dev/null || true

while IFS= read -r manifest_path; do
  case "$manifest_path" in
    skills/*/SKILL.md)
      local_skill="$SKILLS_DIR/${manifest_path#skills/}"
      if [ -f "$local_skill" ] || [ -L "$local_skill" ]; then
        rm -f "$local_skill"
        rmdir "$(dirname "$local_skill")" 2>/dev/null || true
        REMOVED=$((REMOVED + 1))
      fi
      ;;
  esac
done <<< "$(manifest_files)"
rmdir "$SKILLS_DIR" 2>/dev/null || true
rmdir "$(dirname "$SKILLS_DIR")" 2>/dev/null || true

for f in ${EXTRA_FILES[@]+"${EXTRA_FILES[@]}"}; do
  rm -f "$f"
  REMOVED=$((REMOVED + 1))
done

if [ "$PLATFORM" = "codex" ]; then
  if [ -f "AGENTS.md" ]; then
    remove_agents_md_block "AGENTS.md"
    echo "  $REMOVE_AGENTS_MD_NOTE"
    case "$REMOVE_AGENTS_MD_NOTE" in
      🗑*) REMOVED=$((REMOVED + 1)) ;;
    esac
  fi

  # `.codex/config.toml` is install-once and user-owned after install.
  # Prompt on uninstall so Writ can clean fresh installs without silently
  # deleting hand-authored Codex configuration.
  if [ -f "$PLATFORM_DIR/config.toml" ]; then
    printf '⚠️  .codex/config.toml is your Codex configuration (may contain user customizations). Remove it? [y/N] '
    read -r remove_codex_config || remove_codex_config=""
    case "$remove_codex_config" in
      y|Y|yes|YES)
        rm -f "$PLATFORM_DIR/config.toml"
        echo "  🗑  Removed: .codex/config.toml (user-confirmed)"
        REMOVED=$((REMOVED + 1))
        ;;
      *)
        echo "  ⚡ Preserved: .codex/config.toml (kept by user; remove manually if desired)"
        ;;
    esac
  fi
fi

if [ "$HAS_MANIFEST" = true ]; then
  rm -f "$PLATFORM_DIR/.writ-manifest"
  REMOVED=$((REMOVED + 1))
fi

# Remove rules dir if empty (Cursor)
[ "$PLATFORM" = "cursor" ] && rmdir "$PLATFORM_DIR/rules" 2>/dev/null || true
rmdir "$PLATFORM_DIR" 2>/dev/null || true

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
  git add -u "$SKILLS_DIR/" 2>/dev/null || true
  if [ "$PLATFORM" = "claude" ]; then
    git add -u "CLAUDE.md" 2>/dev/null || true
  elif [ "$PLATFORM" = "codex" ]; then
    git add -u "AGENTS.md" 2>/dev/null || true
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

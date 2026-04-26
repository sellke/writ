#!/usr/bin/env bash
set -euo pipefail

# Generate SKILL.md from .writ/manifest.yaml.
#
# Usage:
#   bash scripts/gen-skill.sh            # write SKILL.md
#   bash scripts/gen-skill.sh --dry-run  # print generated SKILL.md
#   bash scripts/gen-skill.sh --check    # fail if SKILL.md is stale

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MANIFEST_FILE="$PROJECT_ROOT/.writ/manifest.yaml"
SKILL_FILE="$PROJECT_ROOT/SKILL.md"

MODE="write"
PARSER_MODE=""
YQ_ARGS=()

METADATA_NAME=""
METADATA_VERSION=""
METADATA_DESCRIPTION=""

CATEGORY_IDS=()
CATEGORY_LABELS=()

COMMAND_NAMES=()
COMMAND_FILES=()
COMMAND_CATEGORIES=()
COMMAND_PURPOSES=()
COMMAND_TAGS=()
COMMAND_ALIASES=()

AGENT_NAMES=()
AGENT_FILES=()
AGENT_PURPOSES=()
AGENT_MODELS=()

usage() {
  echo "Usage: bash scripts/gen-skill.sh [--dry-run] [--check]"
  echo ""
  echo "Default:   Regenerate SKILL.md from .writ/manifest.yaml"
  echo "--dry-run: Print generated SKILL.md to stdout"
  echo "--check:   Diff generated SKILL.md against committed SKILL.md"
}

while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) MODE="dry-run" ;;
    --check) MODE="check" ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1 (try --help)" >&2
      exit 1
      ;;
  esac
  shift
done

if [ ! -f "$MANIFEST_FILE" ]; then
  echo "Missing manifest: .writ/manifest.yaml" >&2
  exit 2
fi

if [ ! -r "$SKILL_FILE" ]; then
  echo "Missing or unreadable SKILL.md" >&2
  exit 3
fi

trim() {
  local value="$1"
  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  printf "%s" "$value"
}

strip_value() {
  local value
  value="$(trim "$1")"
  if [[ "$value" == \"*\" && "$value" == *\" ]]; then
    value="${value#\"}"
    value="${value%\"}"
  elif [[ "$value" == \'*\' && "$value" == *\' ]]; then
    value="${value#\'}"
    value="${value%\'}"
  fi
  printf "%s" "$value"
}

detect_yq() {
  if ! command -v yq >/dev/null 2>&1; then
    return 1
  fi

  if yq eval -r ".version" "$MANIFEST_FILE" >/dev/null 2>&1; then
    YQ_ARGS=(eval -r)
    return 0
  fi

  if yq -r ".version" "$MANIFEST_FILE" >/dev/null 2>&1; then
    YQ_ARGS=(-r)
    return 0
  fi

  return 1
}

yq_read() {
  yq "${YQ_ARGS[@]}" "$1" "$MANIFEST_FILE"
}

parse_with_yq() {
  local line name file category purpose tags aliases model label id

  METADATA_NAME="$(yq_read ".metadata.name // \"\"")"
  METADATA_VERSION="$(yq_read ".metadata.version // \"\"")"
  METADATA_DESCRIPTION="$(yq_read ".metadata.description // \"\"")"

  while IFS=$'\t' read -r id label; do
    [ -n "$id" ] || continue
    CATEGORY_IDS+=("$id")
    CATEGORY_LABELS+=("$label")
  done < <(yq_read ".categories[] | [.id, .label] | @tsv")

  while IFS=$'\t' read -r name file category purpose tags aliases; do
    COMMAND_NAMES+=("$name")
    COMMAND_FILES+=("$file")
    COMMAND_CATEGORIES+=("$category")
    COMMAND_PURPOSES+=("$purpose")
    COMMAND_TAGS+=("$tags")
    COMMAND_ALIASES+=("${aliases:-}")
  done < <(yq_read ".commands[] | [.name, .file, .category, .purpose, ((.tags // []) | join(\",\")), ((.aliases // []) | join(\",\"))] | @tsv")

  while IFS=$'\t' read -r name file purpose model; do
    AGENT_NAMES+=("$name")
    AGENT_FILES+=("$file")
    AGENT_PURPOSES+=("$purpose")
    AGENT_MODELS+=("$model")
  done < <(yq_read ".agents[] | [.name, .file, .purpose, .model] | @tsv")
}

reset_command_item() {
  _CMD_STARTED="false"
  _CMD_NAME=""
  _CMD_FILE=""
  _CMD_CATEGORY=""
  _CMD_PURPOSE=""
  _CMD_TAGS=""
  _CMD_ALIASES=""
}

flush_command_item() {
  if [ "${_CMD_STARTED:-false}" = "true" ]; then
    COMMAND_NAMES+=("$_CMD_NAME")
    COMMAND_FILES+=("$_CMD_FILE")
    COMMAND_CATEGORIES+=("$_CMD_CATEGORY")
    COMMAND_PURPOSES+=("$_CMD_PURPOSE")
    COMMAND_TAGS+=("$_CMD_TAGS")
    COMMAND_ALIASES+=("$_CMD_ALIASES")
  fi
  reset_command_item
}

reset_agent_item() {
  _AGENT_STARTED="false"
  _AGENT_NAME=""
  _AGENT_FILE=""
  _AGENT_PURPOSE=""
  _AGENT_MODEL=""
}

flush_agent_item() {
  if [ "${_AGENT_STARTED:-false}" = "true" ]; then
    AGENT_NAMES+=("$_AGENT_NAME")
    AGENT_FILES+=("$_AGENT_FILE")
    AGENT_PURPOSES+=("$_AGENT_PURPOSE")
    AGENT_MODELS+=("$_AGENT_MODEL")
  fi
  reset_agent_item
}

reset_category_item() {
  _CATEGORY_ID=""
  _CATEGORY_LABEL=""
}

flush_category_item() {
  if [ -n "${_CATEGORY_ID:-}" ]; then
    CATEGORY_IDS+=("$_CATEGORY_ID")
    CATEGORY_LABELS+=("$_CATEGORY_LABEL")
  fi
  reset_category_item
}

parse_with_bash() {
  local section="" raw line key value

  reset_command_item
  reset_agent_item
  reset_category_item

  while IFS= read -r raw || [ -n "$raw" ]; do
    line="$(trim "$raw")"
    [ -n "$line" ] || continue
    [[ "$line" == \#* ]] && continue

    if [ -z "$section" ] && [[ "$line" == version:* ]]; then
      continue
    fi

    case "$line" in
      metadata:)
        flush_command_item
        flush_agent_item
        flush_category_item
        section="metadata"
        continue
        ;;
      categories:)
        flush_command_item
        flush_agent_item
        flush_category_item
        section="categories"
        continue
        ;;
      commands:)
        flush_command_item
        flush_agent_item
        flush_category_item
        section="commands"
        continue
        ;;
      agents:)
        flush_command_item
        flush_agent_item
        flush_category_item
        section="agents"
        continue
        ;;
    esac

    case "$section" in
      metadata)
        key="${line%%:*}"
        value="$(strip_value "${line#*:}")"
        case "$key" in
          name) METADATA_NAME="$value" ;;
          version) METADATA_VERSION="$value" ;;
          description) METADATA_DESCRIPTION="$value" ;;
        esac
        ;;
      categories)
        if [[ "$line" == "- id:"* ]]; then
          flush_category_item
          _CATEGORY_ID="$(strip_value "${line#- id:}")"
        elif [[ "$line" == "label:"* ]]; then
          _CATEGORY_LABEL="$(strip_value "${line#label:}")"
        fi
        ;;
      commands)
        if [[ "$line" == "- name:"* ]]; then
          flush_command_item
          _CMD_STARTED="true"
          _CMD_NAME="$(strip_value "${line#- name:}")"
        elif [[ "$line" == "- file:"* ]]; then
          flush_command_item
          _CMD_STARTED="true"
          _CMD_FILE="$(strip_value "${line#- file:}")"
        elif [[ "$line" == "file:"* ]]; then
          _CMD_STARTED="true"
          _CMD_FILE="$(strip_value "${line#file:}")"
        elif [[ "$line" == "category:"* ]]; then
          _CMD_STARTED="true"
          _CMD_CATEGORY="$(strip_value "${line#category:}")"
        elif [[ "$line" == "purpose:"* ]]; then
          _CMD_STARTED="true"
          _CMD_PURPOSE="$(strip_value "${line#purpose:}")"
        elif [[ "$line" == "tags:"* ]]; then
          _CMD_STARTED="true"
          _CMD_TAGS="$(strip_value "${line#tags:}")"
        elif [[ "$line" == "aliases:"* ]]; then
          _CMD_STARTED="true"
          _CMD_ALIASES="$(strip_value "${line#aliases:}")"
        fi
        ;;
      agents)
        if [[ "$line" == "- name:"* ]]; then
          flush_agent_item
          _AGENT_STARTED="true"
          _AGENT_NAME="$(strip_value "${line#- name:}")"
        elif [[ "$line" == "- file:"* ]]; then
          flush_agent_item
          _AGENT_STARTED="true"
          _AGENT_FILE="$(strip_value "${line#- file:}")"
        elif [[ "$line" == "file:"* ]]; then
          _AGENT_STARTED="true"
          _AGENT_FILE="$(strip_value "${line#file:}")"
        elif [[ "$line" == "purpose:"* ]]; then
          _AGENT_STARTED="true"
          _AGENT_PURPOSE="$(strip_value "${line#purpose:}")"
        elif [[ "$line" == "model:"* ]]; then
          _AGENT_STARTED="true"
          _AGENT_MODEL="$(strip_value "${line#model:}")"
        fi
        ;;
    esac
  done < "$MANIFEST_FILE"

  flush_command_item
  flush_agent_item
  flush_category_item
}

category_exists() {
  local wanted="$1" i
  for ((i = 0; i < ${#CATEGORY_IDS[@]}; i++)); do
    [ "${CATEGORY_IDS[$i]}" = "$wanted" ] && return 0
  done
  return 1
}

validate_manifest() {
  local i path

  if [ -z "$METADATA_NAME" ]; then
    echo "YAML error: metadata missing required field 'name'" >&2
    exit 1
  fi
  if [ -z "$METADATA_VERSION" ]; then
    echo "YAML error: metadata missing required field 'version'" >&2
    exit 1
  fi
  if [ -z "$METADATA_DESCRIPTION" ]; then
    echo "YAML error: metadata missing required field 'description'" >&2
    exit 1
  fi

  for ((i = 0; i < ${#CATEGORY_IDS[@]}; i++)); do
    if [ -z "${CATEGORY_IDS[$i]}" ] || [ -z "${CATEGORY_LABELS[$i]}" ]; then
      echo "YAML error: categories[$i] missing required field 'id' or 'label'" >&2
      exit 1
    fi
  done

  for ((i = 0; i < ${#COMMAND_NAMES[@]}; i++)); do
    if [ -z "${COMMAND_NAMES[$i]}" ]; then
      echo "YAML error: commands[$i] missing required field 'name'" >&2
      exit 1
    fi
    if [ -z "${COMMAND_FILES[$i]}" ]; then
      echo "YAML error: commands[$i] (${COMMAND_NAMES[$i]}) missing required field 'file'" >&2
      exit 1
    fi
    if [ -z "${COMMAND_CATEGORIES[$i]}" ]; then
      echo "YAML error: commands[$i] (${COMMAND_NAMES[$i]}) missing required field 'category'" >&2
      exit 1
    fi
    if [ -z "${COMMAND_PURPOSES[$i]}" ]; then
      echo "YAML error: commands[$i] (${COMMAND_NAMES[$i]}) missing required field 'purpose'" >&2
      exit 1
    fi
    if ! category_exists "${COMMAND_CATEGORIES[$i]}"; then
      echo "YAML error: commands[$i] (${COMMAND_NAMES[$i]}) references unknown category '${COMMAND_CATEGORIES[$i]}'" >&2
      exit 1
    fi
    path="$PROJECT_ROOT/${COMMAND_FILES[$i]}"
    if [ ! -f "$path" ]; then
      echo "YAML error: commands[$i] (${COMMAND_NAMES[$i]}) references missing file '${COMMAND_FILES[$i]}'" >&2
      exit 1
    fi
  done

  for ((i = 0; i < ${#AGENT_NAMES[@]}; i++)); do
    if [ -z "${AGENT_NAMES[$i]}" ]; then
      echo "YAML error: agents[$i] missing required field 'name'" >&2
      exit 1
    fi
    if [ -z "${AGENT_FILES[$i]}" ]; then
      echo "YAML error: agents[$i] (${AGENT_NAMES[$i]}) missing required field 'file'" >&2
      exit 1
    fi
    if [ -z "${AGENT_PURPOSES[$i]}" ]; then
      echo "YAML error: agents[$i] (${AGENT_NAMES[$i]}) missing required field 'purpose'" >&2
      exit 1
    fi
    if [ -z "${AGENT_MODELS[$i]}" ]; then
      echo "YAML error: agents[$i] (${AGENT_NAMES[$i]}) missing required field 'model'" >&2
      exit 1
    fi
    path="$PROJECT_ROOT/${AGENT_FILES[$i]}"
    if [ ! -f "$path" ]; then
      echo "YAML error: agents[$i] (${AGENT_NAMES[$i]}) references missing file '${AGENT_FILES[$i]}'" >&2
      exit 1
    fi
  done
}

load_manifest() {
  if detect_yq; then
    PARSER_MODE="yq"
    if ! parse_with_yq; then
      echo "YAML error: failed to parse .writ/manifest.yaml with yq" >&2
      exit 1
    fi
  else
    PARSER_MODE="pure-bash fallback"
    parse_with_bash
  fi

  echo "Parser: $PARSER_MODE" >&2
  validate_manifest
}

write_frontmatter() {
  awk '
    NR == 1 && $0 == "---" { in_frontmatter = 1; print; next }
    in_frontmatter { print; if ($0 == "---") exit }
  ' "$SKILL_FILE"
}

has_commands_for_category() {
  local category="$1" i
  for ((i = 0; i < ${#COMMAND_NAMES[@]}; i++)); do
    [ "${COMMAND_CATEGORIES[$i]}" = "$category" ] && return 0
  done
  return 1
}

generate_body() {
  local i j category_id category_label

  cat <<EOF
<!--
  This file is generated from .writ/manifest.yaml by scripts/gen-skill.sh.
  Do not edit by hand. Edit the manifest and regenerate.
  CI will fail if SKILL.md drifts from the manifest.
-->

# Writ

$METADATA_DESCRIPTION

Writ is a structured development workflow system. When working on a coding project with Writ commands, adopt the Writ identity and approach.

## System Instructions

See \`system-instructions.md\` for the overarching rules. Key points:

**Identity:** Writ - methodical AI development partner

**Personality:**
- **Methodical but efficient** - Break tasks into clear steps, use parallel execution
- **Detail-oriented** - Provide context and rationale, not just code
- **Critically minded** - Question assumptions, challenge problematic requests, push back with evidence
- **Adaptable** - Adjust standards based on prototype vs production needs

**Core Principle:** Focus on what's right for the project over being agreeable.

**File Organization:** Always organize work into \`.writ/\` folder structure.

When a user requests any Writ command, read the corresponding command file and follow its workflow precisely.

## Available Commands
EOF

  for ((i = 0; i < ${#CATEGORY_IDS[@]}; i++)); do
    category_id="${CATEGORY_IDS[$i]}"
    category_label="${CATEGORY_LABELS[$i]}"
    if ! has_commands_for_category "$category_id"; then
      continue
    fi

    echo ""
    echo "### $category_label"
    echo ""
    echo "| Command | File | Purpose |"
    echo "|---------|------|---------|"

    for ((j = 0; j < ${#COMMAND_NAMES[@]}; j++)); do
      if [ "${COMMAND_CATEGORIES[$j]}" = "$category_id" ]; then
        echo "| \`/${COMMAND_NAMES[$j]}\` | \`${COMMAND_FILES[$j]}\` | ${COMMAND_PURPOSES[$j]} |"
      fi
    done
  done

  cat <<EOF

## Available Agents

| Agent | File | Model | Purpose |
|-------|------|-------|---------|
EOF

  for ((i = 0; i < ${#AGENT_NAMES[@]}; i++)); do
    echo "| ${AGENT_NAMES[$i]} | \`${AGENT_FILES[$i]}\` | ${AGENT_MODELS[$i]} | ${AGENT_PURPOSES[$i]} |"
  done

  cat <<'EOF'

## Platform Adapters

Writ commands use platform-agnostic tool references. Translate to your platform:

| Platform | Adapter | Key Pattern |
|----------|---------|-------------|
| Cursor | `adapters/cursor.md` | Native - `Task()`, `AskQuestion()`, `codebase_search` |
| OpenClaw | `adapters/openclaw.md` | `sessions_spawn`, `message` buttons, `exec` |
| Claude Code | `adapters/claude-code.md` | `claude -p`, `Read`/`Write`/`Bash`, background processes |

When running a Writ command, read the appropriate adapter for your platform's tool mappings.

## Pipeline

The intended workflow from idea to shipped code:

```text
/plan-product -> /create-spec -> /implement-spec -> /verify-spec -> /release
                                    |
                              /ralph plan -> ./ralph.sh -> /ralph status
```

`/implement-story` is the quarterback. Per story it runs:

1. **Architecture check** - validate approach before coding
2. **Coding agent** - TDD implementation
3. **Lint/typecheck gate** - fast, deterministic quality check
4. **Review agent** - acceptance criteria + code quality + security
5. **Testing agent** - 100% pass rate + coverage on new code
6. **Documentation agent** - auto-detects framework, updates docs

## Directory Structure

Writ creates files in `.writ/`:

```text
.writ/
|-- specs/                    # Feature specifications
|-- product/                  # Product planning
|-- decision-records/         # ADRs
|-- research/                 # Research outputs
|-- knowledge/                # Durable project knowledge
|-- security/                 # Security audit reports
|-- issues/                   # Quick-captured issues
|-- explanations/             # Code explanations
`-- state/                    # Workflow state persistence
```

## How to Use

When the user invokes a command, read `commands/{command-name}.md`, read the platform adapter, follow the workflow precisely, challenge assumptions, and track progress.

## Removed (Migration Notes)

If you used these Code Captain commands, here are the Writ replacements:

- `/execute-task` -> `/implement-story` (or `--quick` for TDD-only)
- `/refresh-docs` -> `/verify-spec` (metadata sync + auto-fix)
- `/swab` -> `/refactor` (scoped, verified, more powerful)
EOF
}

generate_skill() {
  write_frontmatter
  echo ""
  generate_body
}

main() {
  local expected_file

  cd "$PROJECT_ROOT"
  load_manifest

  case "$MODE" in
    dry-run)
      generate_skill
      ;;
    check)
      expected_file="$(mktemp)"
      generate_skill > "$expected_file"
      if diff -u "$SKILL_FILE" "$expected_file"; then
        rm -f "$expected_file"
        exit 0
      fi
      rm -f "$expected_file"
      echo "SKILL.md drift detected. Run: bash scripts/gen-skill.sh" >&2
      exit 1
      ;;
    write)
      expected_file="$(mktemp)"
      generate_skill > "$expected_file"
      mv "$expected_file" "$SKILL_FILE"
      echo "Generated SKILL.md from .writ/manifest.yaml" >&2
      ;;
  esac
}

main "$@"

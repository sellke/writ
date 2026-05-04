#!/usr/bin/env bash
set -euo pipefail

# scripts/lint-skill.sh — Boundary lint for Writ skills.
#
# Enforces the role convention from ADR-009: skills describe a capability,
# not a workflow and not a role. Used by /new-skill at authoring time and by
# /refresh-command for batch checking of existing skills.
#
# Usage:
#   bash scripts/lint-skill.sh <path-to-SKILL.md> [<path>...]
#   bash scripts/lint-skill.sh skills/*/SKILL.md
#
# Exit codes:
#   0  All files passed lint
#   1  One or more files have violations
#   2  Usage error (no files, file not found)

usage() {
  echo "Usage: bash scripts/lint-skill.sh <path-to-SKILL.md> [<path>...]" >&2
  echo "" >&2
  echo "Lints SKILL.md files against the ADR-009 role convention:" >&2
  echo "  - Description must be a verb-phrase (not 'Acts as', 'Run the full', ...)" >&2
  echo "  - Body must not invoke commands, skills, subagents, or slash commands" >&2
  exit 2
}

if [ $# -eq 0 ]; then
  usage
fi

# ---------- Description-shape rejection grammar ----------
# Format per row: "PATTERN_PREFIX<TAB>category<TAB>remediation"
# (Tab separator avoids collision with `|` characters inside regex alternations.)
DESC_PATTERNS=(
  $'Acts as\tRole-shape\tSkills describe a capability, not a role. Rephrase as a verb-phrase, or move this to an agent.'
  $'Is responsible for\tRole-shape\tSkills are tools, not responsibilities. Rephrase as \'How to <verb> ...\'.'
  $'The .* agent\tRole-shape\tSkills are not roles. Rephrase as a verb-phrase, or move this to an agent.'
  $'Run the full\tWorkflow-shape\tSkills describe a capability, not a workflow. Move this to a /command.'
  $'Execute the entire\tWorkflow-shape\tSkills are not workflows. Inline the steps as \'How to ...\' or move this to a /command.'
)

# ---------- Body-shape rejection grammar ----------
# Each row is "regex<TAB>category<TAB>remediation"
BODY_PATTERNS=(
  $'Read commands/\tCommand invocation\tSkills do not invoke commands. Inline the steps or describe the capability.'
  $'Read skills/\tSkill chaining\tSkills do not call other skills. Combine them into the consumer (agent/command) that uses both.'
  $'(^|[^A-Za-z_])Task\\(\tSubagent dispatch\tSkills do not spawn subagents. Move orchestration to a command.'
  $'^/[a-z][a-z-]+\tSlash command\tSkills do not invoke slash commands. Skills are tools the agent already has.'
)

TOTAL_VIOLATIONS=0

# Parse the description: line from YAML frontmatter (strip quotes).
extract_description() {
  awk '
    /^---/ { fm = !fm; next }
    fm && /^description:/ {
      sub(/^description:[[:space:]]*/, "")
      gsub(/^["'"'"']|["'"'"']$/, "")
      print
      exit
    }
  ' "$1"
}

# Lint a single SKILL.md.
lint_file() {
  local file="$1"
  local violations=0
  local description category remediation pattern prefix
  local line_num in_codeblock paragraph_chars line trimmed

  if [ ! -f "$file" ]; then
    echo "❌ $file: file not found" >&2
    return 2
  fi

  description=$(extract_description "$file")
  if [ -z "$description" ]; then
    echo "❌ $file: missing or empty 'description:' frontmatter field"
    violations=$((violations + 1))
  else
    for entry in "${DESC_PATTERNS[@]}"; do
      prefix=${entry%%$'\t'*}
      rest=${entry#*$'\t'}
      category=${rest%%$'\t'*}
      remediation=${rest#*$'\t'}
      if [[ "$description" =~ ^$prefix ]]; then
        echo "❌ $file:description: $category — pattern \"$prefix\""
        echo "   Description: \"$description\""
        echo "   Remediation: $remediation"
        violations=$((violations + 1))
      fi
    done
  fi

  in_codeblock=false
  line_num=0
  paragraph_chars=0
  while IFS= read -r line || [ -n "$line" ]; do
    line_num=$((line_num + 1))

    trimmed=${line#"${line%%[![:space:]]*}"}
    if [[ "$trimmed" == '```'* ]]; then
      if [ "$in_codeblock" = true ]; then
        in_codeblock=false
      else
        in_codeblock=true
      fi
      paragraph_chars=0
      continue
    fi

    if [ "$in_codeblock" = true ]; then
      continue
    fi

    if [[ "$line" =~ ^[[:space:]]{4,} ]]; then
      paragraph_chars=0
      continue
    fi

    if [ -z "$trimmed" ]; then
      paragraph_chars=0
      continue
    fi

    if [ $paragraph_chars -ge 200 ]; then
      continue
    fi

    paragraph_chars=$((paragraph_chars + ${#line}))

    for entry in "${BODY_PATTERNS[@]}"; do
      pattern=${entry%%$'\t'*}
      rest=${entry#*$'\t'}
      category=${rest%%$'\t'*}
      remediation=${rest#*$'\t'}
      if [[ "$line" =~ $pattern ]]; then
        echo "❌ $file:$line_num: $category — pattern \"$pattern\""
        echo "   Line: $line"
        echo "   Remediation: $remediation"
        violations=$((violations + 1))
      fi
    done
  done < <(awk 'BEGIN{fm=0;skip=1} /^---/{fm++; if(fm==2){skip=0; next}; next} !skip{print}' "$file")

  if [ $violations -eq 0 ]; then
    echo "✅ $file: clean"
  fi

  TOTAL_VIOLATIONS=$((TOTAL_VIOLATIONS + violations))
  return 0
}

for arg in "$@"; do
  lint_file "$arg"
done

if [ $TOTAL_VIOLATIONS -gt 0 ]; then
  echo ""
  echo "❌ $TOTAL_VIOLATIONS lint violation(s) found across input files"
  exit 1
fi
exit 0

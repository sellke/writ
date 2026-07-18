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
  echo "  - Any declared model_tier value (skill frontmatter, agent config block," >&2
  echo "    or command prose note) must be 'orchestration', 'capability', or a" >&2
  echo "    reserved negative offset (e.g. -1) — see ADR-016" >&2
  echo "    (skill/command values are advisory only — they run at the session/" >&2
  echo "    caller model; only an agent's model_tier is enforced at spawn)" >&2
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

# ---------- Lifecycle vocabulary (ADR-014) ----------
# status: is a closed three-state vocabulary. Evidence entry `type:` is a
# closed four-value vocabulary. State is EARNED from evidence, proven statically
# from the frontmatter alone (no git history, no network):
#   candidate  — 0+ evidence entries (born state from /new-skill)
#   proven     — >=3 well-formed evidence entries
#   promoted   — proven bar PLUS >=1 evidence entry of type: promotion
LIFECYCLE_VIOLATIONS=0

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

# Print the frontmatter body (lines between the first two `---` fences).
extract_frontmatter() {
  awk '
    BEGIN { fm = 0 }
    /^---[[:space:]]*$/ { fm++; if (fm >= 2) exit; next }
    fm == 1 { print }
  ' "$1"
}

_lc_trim() {
  local v="$1"
  v="${v#"${v%%[![:space:]]*}"}"
  v="${v%"${v##*[![:space:]]}"}"
  printf '%s' "$v"
}

_lc_is_type() {
  case "$1" in
    usage|transcript|eval|promotion) return 0 ;;
    *) return 1 ;;
  esac
}

# Emit a lifecycle finding in the shared finding format and count it.
_lc_finding() {
  local file="$1" category="$2" detail="$3" remediation="$4"
  echo "❌ $file: $category — $detail"
  echo "   Remediation: $remediation"
  LIFECYCLE_VIOLATIONS=$((LIFECYCLE_VIOLATIONS + 1))
}

# Validate the current in-progress evidence entry (globals _LC_*), emitting an
# L5 finding naming the first missing/invalid field. Key-based, so reordered
# keys are fine. Counts promotion-typed entries.
_lc_flush_entry() {
  [ "${_LC_ACTIVE:-0}" = 1 ] || return 0
  local bad=""
  if ! [[ "$_LC_DATE" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
    bad="date"
  elif ! _lc_is_type "$_LC_TYPE"; then
    bad="type"
  elif [ -z "$_LC_REF" ]; then
    bad="ref"
  elif [ -z "$_LC_NOTE" ]; then
    bad="note"
  fi
  if [ -n "$bad" ]; then
    _lc_finding "$_LC_FILE" "Lifecycle-evidence" \
      "evidence entry $_LC_ENTRY_COUNT has a missing or invalid '$bad' field" \
      "Each evidence entry needs date (YYYY-MM-DD), type (usage|transcript|eval|promotion), ref, and note."
  fi
  [ "$_LC_TYPE" = "promotion" ] && _LC_PROMOTIONS=$((_LC_PROMOTIONS + 1))
  _LC_ACTIVE=0
}

# Parse a `key: value` fragment into the current evidence entry.
_lc_parse_kv() {
  local kv="$1" k v
  [[ "$kv" == *:* ]] || return 0
  k="$(_lc_trim "${kv%%:*}")"
  v="$(_lc_trim "${kv#*:}")"
  # strip a single layer of surrounding quotes
  if [[ "$v" == \"*\" && "$v" == *\" ]]; then v="${v#\"}"; v="${v%\"}"; fi
  if [[ "$v" == \'*\' && "$v" == *\' ]]; then v="${v#\'}"; v="${v%\'}"; fi
  case "$k" in
    date) _LC_DATE="$v" ;;
    type) _LC_TYPE="$v" ;;
    ref)  _LC_REF="$v" ;;
    note) _LC_NOTE="$v" ;;
  esac
}

_lc_reset_entry() {
  _LC_ACTIVE=0
  _LC_DATE=""
  _LC_TYPE=""
  _LC_REF=""
  _LC_NOTE=""
}

# Lifecycle hygiene checks (ADR-014). Sets LIFECYCLE_VIOLATIONS.
lint_lifecycle() {
  local file="$1"
  LIFECYCLE_VIOLATIONS=0
  _LC_FILE="$file"

  local fm status status_present line rest_trimmed trimmed item
  local in_evidence=0
  _LC_ENTRY_COUNT=0
  _LC_PROMOTIONS=0
  _lc_reset_entry

  fm="$(extract_frontmatter "$file")"

  # L1 — status present?
  if ! printf '%s\n' "$fm" | grep -q '^status:'; then
    _lc_finding "$file" "Lifecycle-missing" \
      "missing lifecycle status" \
      "Add 'status: candidate' (or proven|promoted with evidence) to the frontmatter. See ADR-014."
    return 0
  fi

  status="$(printf '%s\n' "$fm" | awk '/^status:/{sub(/^status:[[:space:]]*/,""); print; exit}')"
  status="$(_lc_trim "$status")"
  if [[ "$status" == \"*\" && "$status" == *\" ]]; then status="${status#\"}"; status="${status%\"}"; fi

  # L2 — value in the closed vocabulary?
  case "$status" in
    candidate|proven|promoted) ;;
    *)
      _lc_finding "$file" "Lifecycle-invalid" \
        "invalid status '$status'; expected candidate|proven|promoted" \
        "Set status to one of the three earned states. See ADR-014."
      return 0
      ;;
  esac

  # candidate needs no evidence — nothing further to prove.
  [ "$status" = "candidate" ] && return 0

  # Parse the evidence block (proven/promoted only). Count list items as
  # entries regardless of well-formedness; validate each entry (L5).
  while IFS= read -r line; do
    if [[ "$line" =~ ^evidence: ]]; then
      rest_trimmed="$(_lc_trim "${line#evidence:}")"
      if [ "$rest_trimmed" = "[]" ]; then
        in_evidence=0
      else
        in_evidence=1
      fi
      continue
    fi

    if [ "$in_evidence" = 1 ]; then
      # A new top-level key (unindented, not a list item) ends the block.
      if [[ "$line" =~ ^[^[:space:]] ]] && [[ ! "$line" =~ ^- ]]; then
        _lc_flush_entry
        in_evidence=0
        continue
      fi

      trimmed="${line#"${line%%[![:space:]]*}"}"
      if [ "$trimmed" = "-" ] || [[ "$trimmed" == "- "* ]]; then
        _lc_flush_entry
        _lc_reset_entry
        _LC_ACTIVE=1
        _LC_ENTRY_COUNT=$((_LC_ENTRY_COUNT + 1))
        item="$(_lc_trim "${trimmed#-}")"
        [ -n "$item" ] && _lc_parse_kv "$item"
        continue
      fi

      [ -n "$trimmed" ] && _lc_parse_kv "$trimmed"
    fi
  done < <(printf '%s\n' "$fm")
  _lc_flush_entry

  # L3 — proven/promoted need >=3 well-formed entries.
  if [ "$_LC_ENTRY_COUNT" -lt 3 ]; then
    _lc_finding "$file" "Lifecycle-unearned" \
      "unearned state: $status requires >=3 evidence entries (found $_LC_ENTRY_COUNT)" \
      "Record at least three well-formed evidence entries before declaring $status, or set status: candidate."
  fi

  # L4 — promoted needs a promotion record.
  if [ "$status" = "promoted" ] && [ "$_LC_PROMOTIONS" -lt 1 ]; then
    _lc_finding "$file" "Lifecycle-unearned" \
      "unearned state: promoted requires a type: promotion evidence entry" \
      "Add an evidence entry of type: promotion citing the consumer whose required_skills declares this skill."
  fi
}

# ---------- model_tier value validation (ADR-016) ----------
# Advisory (skills, command prose notes) and enforced (agent config blocks)
# model_tier declarations share one allowed-value grammar. This check is
# format-agnostic and scans the ENTIRE raw file (unlike extract_frontmatter,
# which is fence-gated) — it recognizes two shapes:
#   1. Key-value:   model_tier: <value>            (skill frontmatter, agent
#                    Agent Configuration/Specification blocks)
#   2. Locked prose: **Model tier (advisory only):** <value>
#                    (the exact command prose-note format committed in
#                    system-instructions.md)
# A trailing `# comment` or descriptive prose after the value is not part of
# the value itself — the capture stops at the first non-identifier character,
# which naturally strips comments/whitespace/placeholder markup.
MODEL_TIER_VIOLATIONS=0

lint_model_tier() {
  local file="$1"
  local line line_num=0 value
  MODEL_TIER_VIOLATIONS=0

  while IFS= read -r line || [ -n "$line" ]; do
    line_num=$((line_num + 1))
    value=""

    if [[ "$line" =~ model_tier:[[:space:]]*([A-Za-z0-9-]+) ]]; then
      value="${BASH_REMATCH[1]}"
    elif [[ "$line" =~ Model[[:space:]]tier[[:space:]]\(advisory[[:space:]]only\):\*{0,2}[[:space:]]*([A-Za-z0-9-]+) ]]; then
      value="${BASH_REMATCH[1]}"
    else
      continue
    fi

    if ! [[ "$value" =~ ^(orchestration|capability|-[0-9]+)$ ]]; then
      echo "❌ $file:$line_num: model_tier '$value' is invalid. Use 'orchestration', 'capability', or a reserved negative offset (e.g. -1)."
      MODEL_TIER_VIOLATIONS=$((MODEL_TIER_VIOLATIONS + 1))
    fi
  done < "$file"
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

  lint_model_tier "$file"
  violations=$((violations + MODEL_TIER_VIOLATIONS))

  lint_lifecycle "$file"
  violations=$((violations + LIFECYCLE_VIOLATIONS))

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

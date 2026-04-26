#!/usr/bin/env bash
set -euo pipefail

# Run Writ Tier 1 static checks.
#
# Usage:
#   bash scripts/eval.sh
#   bash scripts/eval.sh --check=preamble
#   bash scripts/eval.sh --report=eval-report.md
#   bash scripts/eval.sh --check=preamble --fix

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

CHECK="all"
FIX=false
REPORT_PATH=""

CHECKS=(
  required-sections
  anti-sycophancy
  prime-directive-sync
  broken-refs
  length
  manifest
  preamble
  owner
)

TOTAL_FINDINGS=0
RUN_ERRORS=0
CURRENT_CHECK=""
CURRENT_FINDINGS=0
CHECK_TMP=""

usage() {
  echo "Usage: bash scripts/eval.sh [--check=NAME] [--report=PATH] [--fix]"
  echo ""
  echo "Default:       Run all checks and write a markdown report to .writ/state/"
  echo "--check=NAME:  Run one check: ${CHECKS[*]}"
  echo "--report=PATH: Write report to PATH instead of the default"
  echo "--fix:         Apply supported auto-fixes (currently: preamble)"
}

while [ $# -gt 0 ]; do
  case "$1" in
    --check=*)
      CHECK="${1#--check=}"
      ;;
    --report=*)
      REPORT_PATH="${1#--report=}"
      ;;
    --fix)
      FIX=true
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1 (try --help)" >&2
      exit 2
      ;;
  esac
  shift
done

check_exists() {
  local wanted="$1" check
  [ "$wanted" = "all" ] && return 0

  for check in "${CHECKS[@]}"; do
    [ "$check" = "$wanted" ] && return 0
  done

  return 1
}

if ! check_exists "$CHECK"; then
  echo "Unknown check: $CHECK" >&2
  usage >&2
  exit 2
fi

if [ -z "$REPORT_PATH" ]; then
  mkdir -p "$PROJECT_ROOT/.writ/state"
  REPORT_PATH="$PROJECT_ROOT/.writ/state/eval-$(date -u +%Y%m%d-%H%M%S).md"
elif [[ "$REPORT_PATH" != /* ]]; then
  REPORT_PATH="$PROJECT_ROOT/$REPORT_PATH"
fi

relpath() {
  local path="$1"
  printf "%s" "${path#"$PROJECT_ROOT"/}"
}

line_count() {
  awk 'END { print NR }' "$1"
}

add_finding() {
  local location="$1"
  local message="$2"
  local hint="$3"

  CURRENT_FINDINGS=$((CURRENT_FINDINGS + 1))
  TOTAL_FINDINGS=$((TOTAL_FINDINGS + 1))
  printf -- '- `%s`: %s _Remediation:_ %s\n' "$location" "$message" "$hint" >> "$CHECK_TMP"
}

add_detail() {
  printf "%s\n" "$1" >> "$CHECK_TMP"
}

file_has_exemption() {
  local file="$1"
  local check="$2"

  grep -Eq "eval-exempt:.*($check|all)" "$file"
}

line_is_policy_example() {
  local line="$1"

  [[ "$line" == *"Never pad responses"* ]] && return 0
  [[ "$line" == *"unless the question or point"* ]] && return 0
  [[ "$line" == *"banned phrase"* ]] && return 0
  return 1
}

has_heading() {
  local file="$1"
  local pattern="$2"

  grep -Eq "$pattern" "$file"
}

command_files() {
  local file base
  for file in "$PROJECT_ROOT"/commands/*.md; do
    [ -f "$file" ] || continue
    base="$(basename "$file")"
    [[ "$base" == _*.md ]] && continue
    printf "%s\n" "$file"
  done
}

root_agent_files() {
  local file
  for file in "$PROJECT_ROOT"/agents/*.md; do
    [ -f "$file" ] || continue
    printf "%s\n" "$file"
  done
}

spec_lite_files() {
  local rel

  git -C "$PROJECT_ROOT" ls-files -co --exclude-standard -- .writ/specs 2>/dev/null |
    while IFS= read -r rel; do
      case "$rel" in
        */spec-lite.md) printf "%s/%s\n" "$PROJECT_ROOT" "$rel" ;;
      esac
    done
}

check_required_sections() {
  local file rel

  while IFS= read -r file; do
    rel="$(relpath "$file")"
    if file_has_exemption "$file" "required-sections"; then
      continue
    fi

    if ! has_heading "$file" '^## Overview[[:space:]]*$'; then
      add_finding "$rel" "missing section \"## Overview\"." "Add an Overview section near the top of the command."
    fi

    if ! has_heading "$file" '^## (Invocation|Modes)[[:space:]]*$'; then
      add_finding "$rel" "missing section \"## Invocation\" or documented equivalent \"## Modes\"." "Add Invocation examples, or add a targeted eval-exempt comment with a tracking issue."
    fi

    if ! has_heading "$file" '^## (Command Process|[^[:space:]].*Workflow)[[:space:]]*$|^## Phase [0-9]+|^## `/[^`]+`'; then
      add_finding "$rel" "missing section \"## Command Process\" or phase/workflow equivalent." "Add a Command Process section or a clear phase/workflow heading."
    fi
  done < <(command_files)
}

check_anti_sycophancy() {
  local phrase_file="$PROJECT_ROOT/.writ/eval/anti-sycophancy-phrases.txt"
  local file phrase line_no line rel

  if [ ! -r "$phrase_file" ]; then
    RUN_ERRORS=$((RUN_ERRORS + 1))
    add_finding ".writ/eval/anti-sycophancy-phrases.txt" "phrase list is missing or unreadable." "Restore the data file with one literal phrase per line."
    return
  fi

  while IFS= read -r phrase || [ -n "$phrase" ]; do
    [ -n "$phrase" ] || continue
    [[ "$phrase" == \#* ]] && continue

    for file in "$PROJECT_ROOT"/commands/*.md "$PROJECT_ROOT"/agents/*.md "$PROJECT_ROOT/system-instructions.md" "$PROJECT_ROOT/cursor/writ.mdc"; do
      [ -f "$file" ] || continue
      rel="$(relpath "$file")"
      if file_has_exemption "$file" "anti-sycophancy"; then
        continue
      fi

      while IFS=$'\t' read -r line_no line; do
        [ -n "$line_no" ] || continue
        [[ "$line" == *"eval-exempt:"* ]] && continue
        if line_is_policy_example "$line"; then
          continue
        fi
        add_finding "$rel:$line_no" "banned phrase '$phrase'." "Remove empty praise or replace it with verified, specific assessment."
      done < <(awk -v phrase="$phrase" 'index($0, phrase) { print FNR "\t" $0 }' "$file")
    done
  done < "$phrase_file"
}

extract_prime_directive() {
  local file="$1"

  awk '
    /^## Prime Directive[[:space:]]*$/ { capture = 1 }
    capture && /^## [^#]/ && $0 !~ /^## Prime Directive[[:space:]]*$/ { exit }
    capture { print }
  ' "$file"
}

check_prime_directive_sync() {
  local system_tmp cursor_tmp diff_tmp

  system_tmp="$(mktemp)"
  cursor_tmp="$(mktemp)"
  diff_tmp="$(mktemp)"

  extract_prime_directive "$PROJECT_ROOT/system-instructions.md" > "$system_tmp"
  extract_prime_directive "$PROJECT_ROOT/cursor/writ.mdc" > "$cursor_tmp"

  if [ ! -s "$system_tmp" ] || [ ! -s "$cursor_tmp" ]; then
    add_finding "system-instructions.md / cursor/writ.mdc" "Prime Directive section missing in one or both files." "Restore matching ## Prime Directive sections."
  elif ! diff -u "$system_tmp" "$cursor_tmp" > "$diff_tmp"; then
    add_finding "cursor/writ.mdc" "Prime Directive section drift detected." "Make the section byte-identical to system-instructions.md."
    add_detail ""
    add_detail "```diff"
    sed 's/^/    /' "$diff_tmp" >> "$CHECK_TMP"
    add_detail "```"
  fi

  rm -f "$system_tmp" "$cursor_tmp" "$diff_tmp"
}

should_skip_ref_target() {
  local target="$1"

  [[ "$target" == http://* ]] && return 0
  [[ "$target" == https://* ]] && return 0
  [[ "$target" == mailto:* ]] && return 0
  [[ "$target" == \#* ]] && return 0
  [[ "$target" == *"{"* || "$target" == *"}"* ]] && return 0
  [[ "$target" == *"YYYY-MM-DD"* ]] && return 0
  [[ "$target" == "" ]] && return 0
  return 1
}

resolve_ref_target() {
  local file="$1"
  local target="$2"
  local clean dir

  clean="${target%%#*}"
  clean="${clean%%\?*}"

  case "$clean" in
    ./*|../*)
      dir="$(dirname "$file")"
      printf "%s/%s" "$dir" "$clean"
      ;;
    commands/*|agents/*|adapters/*|system-instructions.md|SKILL.md)
      printf "%s/%s" "$PROJECT_ROOT" "$clean"
      ;;
    *)
      dir="$(dirname "$file")"
      printf "%s/%s" "$dir" "$clean"
      ;;
  esac
}

check_broken_refs() {
  local file line_no target resolved rel

  for file in "$PROJECT_ROOT"/commands/*.md "$PROJECT_ROOT"/agents/*.md "$PROJECT_ROOT"/adapters/*.md "$PROJECT_ROOT/system-instructions.md" "$PROJECT_ROOT/SKILL.md"; do
    [ -f "$file" ] || continue
    rel="$(relpath "$file")"
    if file_has_exemption "$file" "broken-refs"; then
      continue
    fi

    while IFS=$'\t' read -r line_no target; do
      [ -n "$line_no" ] || continue
      if should_skip_ref_target "$target"; then
        continue
      fi

      resolved="$(resolve_ref_target "$file" "$target")"
      if [ ! -e "$resolved" ]; then
        add_finding "$rel:$line_no" "broken ref to '$target'." "Fix the markdown link target or remove the stale reference."
      fi
    done < <(awk '
      {
        rest = $0
        while (match(rest, /\]\(([^)]+)\)/)) {
          target = substr(rest, RSTART + 2, RLENGTH - 3)
          print FNR "\t" target
          rest = substr(rest, RSTART + RLENGTH)
        }
      }
    ' "$file")
  done
}

check_length() {
  local file count rel

  while IFS= read -r file; do
    rel="$(relpath "$file")"
    if file_has_exemption "$file" "length"; then
      continue
    fi
    count="$(line_count "$file")"
    if [ "$count" -gt 100 ]; then
      add_finding "$rel" "$count lines (limit 100)." "Trim spec-lite.md to implementation-critical context or add an exemption with a tracking issue."
    fi
  done < <(spec_lite_files)

  file="$PROJECT_ROOT/commands/_preamble.md"
  if [ -f "$file" ] && ! file_has_exemption "$file" "length"; then
    count="$(line_count "$file")"
    if [ "$count" -gt 80 ]; then
      add_finding "commands/_preamble.md" "$count lines (limit 80)." "Move command-specific detail out of the shared preamble."
    fi
  fi

  while IFS= read -r file; do
    rel="$(relpath "$file")"
    if file_has_exemption "$file" "length"; then
      continue
    fi
    count="$(line_count "$file")"
    if [ "$count" -gt 2000 ]; then
      add_finding "$rel" "$count lines (limit 2000)." "Split runaway command content or add an exemption with a tracking issue."
    fi
  done < <(command_files)
}

manifest_paths() {
  local section="$1"

  awk -v wanted="$section" '
    /^[^[:space:]][^:]*:/ {
      current = $1
      sub(/:$/, "", current)
      in_section = (current == wanted)
    }
    in_section && /^[[:space:]]*file:/ {
      value = $0
      sub(/^[[:space:]]*file:[[:space:]]*/, "", value)
      gsub(/^"|"$/, "", value)
      gsub(/^'\''|'\''$/, "", value)
      print value
    }
  ' "$PROJECT_ROOT/.writ/manifest.yaml"
}

path_in_file() {
  local needle="$1"
  local list_file="$2"

  grep -Fxq "$needle" "$list_file"
}

check_manifest() {
  local manifest="$PROJECT_ROOT/.writ/manifest.yaml"
  local command_list agent_list path file rel base

  if [ ! -r "$manifest" ]; then
    RUN_ERRORS=$((RUN_ERRORS + 1))
    add_finding ".writ/manifest.yaml" "manifest missing or unreadable." "Restore the manifest generated in Story 3."
    return
  fi

  if ! bash "$PROJECT_ROOT/scripts/gen-skill.sh" --dry-run >/dev/null 2>&1; then
    add_finding ".writ/manifest.yaml" "manifest failed generator validation." "Run bash scripts/gen-skill.sh --dry-run for the parser error, then fix the manifest."
  fi

  command_list="$(mktemp)"
  agent_list="$(mktemp)"
  manifest_paths "commands" > "$command_list"
  manifest_paths "agents" > "$agent_list"

  while IFS= read -r path || [ -n "$path" ]; do
    [ -n "$path" ] || continue
    if [ ! -f "$PROJECT_ROOT/$path" ]; then
      add_finding ".writ/manifest.yaml" "command references missing file '$path'." "Create the file or remove/update the manifest entry."
    fi
  done < "$command_list"

  while IFS= read -r path || [ -n "$path" ]; do
    [ -n "$path" ] || continue
    if [ ! -f "$PROJECT_ROOT/$path" ]; then
      add_finding ".writ/manifest.yaml" "agent references missing file '$path'." "Create the file or remove/update the manifest entry."
    fi
  done < "$agent_list"

  while IFS= read -r file; do
    rel="$(relpath "$file")"
    base="$(basename "$file")"
    [[ "$base" == _*.md ]] && continue
    if ! path_in_file "$rel" "$command_list"; then
      add_finding "$rel" "command file exists but is not listed in .writ/manifest.yaml." "Add the command to the manifest or rename it as an infra file."
    fi
  done < <(command_files)

  while IFS= read -r file; do
    rel="$(relpath "$file")"
    if ! path_in_file "$rel" "$agent_list"; then
      add_finding "$rel" "agent file exists but is not listed in .writ/manifest.yaml." "Add the agent to the manifest or move it out of the root agents directory."
    fi
  done < <(root_agent_files)

  rm -f "$command_list" "$agent_list"
}

append_preamble_reference() {
  local file="$1"

  if grep -Eq '^## References[[:space:]]*$' "$file"; then
    {
      printf "\n"
      printf -- "- Standing instructions: [\`commands/_preamble.md\`](_preamble.md)\n"
    } >> "$file"
  else
    {
      printf "\n---\n\n"
      printf "## References\n\n"
      printf -- "- Standing instructions: [\`commands/_preamble.md\`](_preamble.md)\n"
      printf -- "- Identity & Prime Directive: [\`system-instructions.md\`](../system-instructions.md)\n"
    } >> "$file"
  fi
}

check_preamble() {
  local preamble="$PROJECT_ROOT/commands/_preamble.md"
  local file rel

  if [ ! -s "$preamble" ]; then
    add_finding "commands/_preamble.md" "preamble file is missing or empty." "Restore commands/_preamble.md."
    return
  fi

  while IFS= read -r file; do
    rel="$(relpath "$file")"
    if file_has_exemption "$file" "preamble"; then
      continue
    fi

    if ! grep -Fq "commands/_preamble.md" "$file"; then
      if [ "$FIX" = true ]; then
        append_preamble_reference "$file"
      fi
      add_finding "$rel" "missing reference to commands/_preamble.md." "Run bash scripts/eval.sh --check=preamble --fix or add the References entry manually."
    fi
  done < <(command_files)
}

spec_created_date() {
  local file="$1"
  local date dir

  date="$(git -C "$PROJECT_ROOT" log --diff-filter=A --format=%aI -- "$file" 2>/dev/null | sed -n '$p' || true)"
  if [ -n "$date" ]; then
    printf "%s" "${date:0:10}"
    return
  fi

  dir="$(basename "$(dirname "$file")")"
  if [[ "$dir" =~ ^([0-9]{4}-[0-9]{2}-[0-9]{2}) ]]; then
    printf "%s" "${BASH_REMATCH[1]}"
  fi
}

spec_has_owner() {
  local file="$1"

  awk 'NR <= 30 && ($0 ~ /^[[:space:]]*owner:/ || $0 ~ /\*\*Owner:\*\*/) { found = 1 } END { exit found ? 0 : 1 }' "$file"
}

check_owner() {
  local ship_date="2026-04-24"
  local file created rel

  for file in "$PROJECT_ROOT"/.writ/specs/*/spec.md; do
    [ -f "$file" ] || continue
    rel="$(relpath "$file")"
    if file_has_exemption "$file" "owner"; then
      continue
    fi

    created="$(spec_created_date "$file")"
    [ -n "$created" ] || continue
    if [[ "$created" < "$ship_date" ]]; then
      continue
    fi

    if ! spec_has_owner "$file"; then
      add_finding "$rel" "missing owner metadata for post-ship spec ($created)." "Add owner metadata generated from git config user.name, or document a targeted exemption."
    fi
  done
}

run_check() {
  local check="$1"
  local func="check_${check//-/_}"

  CURRENT_CHECK="$check"
  CURRENT_FINDINGS=0
  CHECK_TMP="$(mktemp)"

  if ! "$func"; then
    RUN_ERRORS=$((RUN_ERRORS + 1))
    add_finding "$check" "check failed to run." "Inspect scripts/eval.sh and rerun the check."
  fi

  {
    echo ""
    echo "## $check"
    echo ""
    if [ "$CURRENT_FINDINGS" -eq 0 ]; then
      echo "PASS"
    else
      echo "FAIL ($CURRENT_FINDINGS finding(s))"
      echo ""
      cat "$CHECK_TMP"
    fi
  } >> "$REPORT_PATH"

  rm -f "$CHECK_TMP"
}

main() {
  local check

  cd "$PROJECT_ROOT"

  {
    echo "# Writ Eval Tier 1 Report"
    echo ""
    echo "- Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "- Mode: $CHECK"
    echo "- Auto-fix: $FIX"
  } > "$REPORT_PATH"

  if [ "$CHECK" = "all" ]; then
    for check in "${CHECKS[@]}"; do
      run_check "$check"
    done
  else
    run_check "$CHECK"
  fi

  {
    echo ""
    echo "## Summary"
    echo ""
    echo "- Findings: $TOTAL_FINDINGS"
    echo "- Run errors: $RUN_ERRORS"
  } >> "$REPORT_PATH"

  echo "Eval report: $(relpath "$REPORT_PATH")"

  if [ "$RUN_ERRORS" -gt 0 ]; then
    exit 2
  fi
  if [ "$TOTAL_FINDINGS" -gt 0 ]; then
    exit 1
  fi
}

main "$@"

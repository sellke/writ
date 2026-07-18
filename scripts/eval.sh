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
  autonomy-governance
  recommendation-semantics
  recommended-spec-implementation
  recommended-staging
  spec-dependencies
  phase-lanes
  phase-challenges
  phase-quarantine
  phase-knowledge
  phase-health
  ralph-retirement
  skill-lifecycle
  refresh-evidence
  knowledge-consolidate
  memory-interop
  leanness
)

TOTAL_FINDINGS=0
RUN_ERRORS=0
CURRENT_CHECK=""
CURRENT_FINDINGS=0
CHECK_TMP=""
CURRENT_NOTES=0
NOTE_TMP=""
CURRENT_SCENARIOS=0
CURRENT_SCENARIOS_PASSED=0
CURRENT_STATIC_ASSERTIONS=0
CURRENT_STATIC_ASSERTIONS_PASSED=0

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

# Non-blocking note/warning: shown in the report even when the check PASSes, and
# never increments findings (so warn-only checks stay exit 0). Used by
# check_leanness for aggregate-weight warnings and the metrics summary.
add_note() {
  CURRENT_NOTES=$((CURRENT_NOTES + 1))
  printf -- '- %s\n' "$1" >> "$NOTE_TMP"
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

require_literal() {
  local file="$1"
  local literal="$2"
  local message="$3"

  if [ ! -f "$file" ] || ! grep -Fq -- "$literal" "$file"; then
    add_finding "$(relpath "$file")" "$message" "Add the exact governance contract without weakening its safety boundaries."
  fi
}

forbid_literal() {
  local file="$1"
  local literal="$2"
  local message="$3"

  if [ -f "$file" ] && grep -Fq -- "$literal" "$file"; then
    add_finding "$(relpath "$file")" "$message" "Replace the superseded active wording while leaving historical ADRs and specs unchanged."
  fi
}

forbid_literal_ci() {
  local file="$1"
  local literal="$2"
  local message="$3"

  if [ -f "$file" ] && grep -Fiq -- "$literal" "$file"; then
    add_finding "$(relpath "$file")" "$message" "Remove the retired reference from the active surface; historical ADRs, specs, and archive/ may keep it."
  fi
}

check_autonomy_governance() {
  local adr="$PROJECT_ROOT/.writ/decision-records/adr-013-recommended-autonomous-delivery.md"
  local delivery_spec="$PROJECT_ROOT/.writ/specs/2026-07-10-recommended-autonomous-delivery/spec.md"
  local phase_spec="$PROJECT_ROOT/.writ/specs/2026-07-09-phase6-autonomy-ceiling/spec.md"
  local phase_lite="$PROJECT_ROOT/.writ/specs/2026-07-09-phase6-autonomy-ceiling/spec-lite.md"
  local phase_story_3="$PROJECT_ROOT/.writ/specs/2026-07-09-phase6-autonomy-ceiling/user-stories/story-3-contract-preserving-user-challenges.md"
  local phase_story_7="$PROJECT_ROOT/.writ/specs/2026-07-09-phase6-autonomy-ceiling/user-stories/story-7-ralph-retirement-and-autonomy-acceptance.md"
  local phase_index="$PROJECT_ROOT/.writ/specs/2026-07-09-phase6-autonomy-ceiling/user-stories/README.md"
  local roadmap="$PROJECT_ROOT/.writ/product/roadmap.md"
  local mission="$PROJECT_ROOT/.writ/product/mission.md"
  local mission_lite="$PROJECT_ROOT/.writ/product/mission-lite.md"
  local ralph_adr="$PROJECT_ROOT/.writ/decision-records/adr-012-ralph-deprecation.md"
  local system="$PROJECT_ROOT/system-instructions.md"
  local cursor_rule="$PROJECT_ROOT/cursor/writ.mdc"

  require_literal "$adr" "Supersedes: Conflicting portions of [ADR-010]" "ADR-013 must explicitly supersede ADR-010's conflicting portions."
  require_literal "$adr" "exact reviewed PR head SHA" "ADR-013 must bind the one production approval to the exact reviewed PR head SHA."
  require_literal "$adr" "private chain-of-thought" "ADR-013 must exclude private chain-of-thought from durable audit summaries."
  require_literal "$adr" '`--recommend` lives on exactly two commands' "ADR-013 must scope --recommend to exactly two commands (create-spec + implement-phase)."
  require_literal "$adr" "branch protection, required reviews, authentication, authorization" "ADR-013 must preserve platform protections and authentication."

  require_literal "$delivery_spec" '> **Blocks:** `2026-07-09-phase6-autonomy-ceiling`' "The recommended-delivery contract must remain an explicit prerequisite to Phase 6."
  require_literal "$delivery_spec" "exact reviewed PR head SHA" "The locked delivery spec must bind production approval to the reviewed SHA."
  require_literal "$delivery_spec" '- Multi-spec `/implement-phase --recommend`' "The locked delivery spec must exclude multi-spec recommended execution."
  require_literal "$delivery_spec" "private chain-of-thought" "The locked delivery spec must exclude private chain-of-thought storage."

  require_literal "$phase_spec" '> **Dependencies:** [2026-07-10-recommended-autonomous-delivery]' "Phase 6 must declare the recommended-delivery spec as its exact dependency."
  require_literal "$phase_lite" "2026-07-10-recommended-autonomous-delivery" "The Phase 6 lite contract must name its recommended-delivery prerequisite."
  require_literal "$phase_story_3" "evidence-based select-or-pause" "Phase 6 Story 3 must use the evidence-based select-or-pause boundary."
  require_literal "$phase_story_7" 'single-spec `--recommend`' "Phase 6 Story 7 must distinguish single-spec recommended delivery from multi-spec phase execution."
  require_literal "$phase_index" "2026-07-10-recommended-autonomous-delivery" "The Phase 6 story index must record the cross-spec prerequisite."

  require_literal "$roadmap" "2026-07-10-recommended-autonomous-delivery" "The roadmap must sequence recommended autonomous delivery before Phase 6."
  require_literal "$roadmap" "never merges, opens PRs, or releases" "The roadmap must record that recommended flows end short of merge/PR/release (ADR-013 as revised 2026-07-17)."

  require_literal "$mission" '`--recommend` adds evidence-backed autonomy on two commands' "The product mission must describe --recommend on exactly two commands (create-spec + implement-phase) per ADR-013 as revised."
  require_literal "$mission_lite" "both ending short of merge/PR/release" "The lite mission must preserve the merge/PR/release boundary for both recommended commands."
  require_literal "$ralph_adr" "[ADR-013]" "ADR-012 must distinguish Ralph retirement from bounded recommended delivery."

  require_literal "$system" 'only when the invoked command explicitly documents support for `--recommend`' "The system policy must limit the exception to commands that explicitly support --recommend."
  require_literal "$system" "observable evidence and durable audit summaries" "The system policy must require observable evidence and durable audit summaries."
  require_literal "$system" "Retain the human production boundary" "The system policy must retain the human production boundary (no --recommend merge/PR/release) per ADR-013 as revised."
  require_literal "$system" '`--recommend` lives on exactly two commands' "The system policy must scope --recommend to exactly two commands (create-spec + implement-phase)."
  require_literal "$system" "branch protection, required checks, authentication, or authorization" "The system policy must preserve platform protection and authentication boundaries."
  require_literal "$system" "exclude private chain-of-thought" "The system policy must keep audit summaries free of private reasoning."
  require_literal "$cursor_rule" 'only when the invoked command explicitly documents support for `--recommend`' "The Cursor rule mirror must preserve the narrow recommended-delivery exception."

  forbid_literal "$phase_spec" "human *in the loop* at contract level" "Phase 6 still contains the superseded contract-level human gate."
  forbid_literal "$phase_spec" "never auto-decided" "Phase 6 still contains unconditional User Challenge decision language."
  forbid_literal "$phase_lite" "Any unattended mode" "The Phase 6 lite contract still forbids all unattended modes rather than opaque unbounded loops."
  forbid_literal "$phase_story_3" "selectable options rather than a local decision" "Phase 6 Story 3 still prohibits evidence-based local selection categorically."
  forbid_literal "$roadmap" "in the loop at contract level" "The roadmap still contains the superseded contract-level human gate."
  forbid_literal "$roadmap" "Never auto-decided." "The roadmap still contains unconditional User Challenge decision language."

  forbid_literal "$system" "exact reviewed PR head SHA" "system-instructions still binds recommended delivery to a SHA-bound production approval; ADR-013 (revised 2026-07-17) defers that flow (preserved only in the ADR and locked delivery spec)."
  forbid_literal "$roadmap" 'Multi-spec `/implement-phase --recommend` remains excluded.' "The roadmap still states the superseded multi-spec exclusion; ADR-013 (revised 2026-07-17) makes /implement-phase --recommend the supported end-to-end loop."
  forbid_literal "$mission_lite" 'single-spec `--recommend` delivery' "mission-lite still frames recommended delivery as single-spec, superseded by ADR-013 as revised 2026-07-17."
}

check_recommendation_semantics() {
  local system="$PROJECT_ROOT/system-instructions.md"
  local cursor_rule="$PROJECT_ROOT/cursor/writ.mdc"
  local cursor_adapter="$PROJECT_ROOT/adapters/cursor.md"
  local claude_adapter="$PROJECT_ROOT/adapters/claude-code.md"
  local codex_adapter="$PROJECT_ROOT/adapters/codex.md"
  local adapter

  require_literal "$system" 'Exactly one option label ends with the literal suffix `(Recommended)`.' "Normal bounded questions must label exactly one recommendation."
  require_literal "$system" 'If options remain explicitly equivalent after simplicity and reversibility analysis, label none and disclose the equivalence.' "Equivalent options must remain unlabeled and be disclosed."
  require_literal "$system" 'Normal mode remains human-selected; the label is advisory.' "Recommendation labels must not change normal interactive control."
  require_literal "$system" 'Option order, affirmative wording, and user inactivity are never evidence.' "Recommendation evidence must not come from presentation or inactivity."
  require_literal "$system" 'governance and safety eligibility → locked artifacts → current repository or provider state → project conventions → simplicity and reversibility' "Recommendation evidence precedence must be domain-scoped and deterministic."
  require_literal "$system" 'Conflicting authoritative evidence pauses the decision.' "Conflicting authoritative evidence must pause."
  require_literal "$system" 'eligible evidence-supported option' "Recommend mode must automatically select only an eligible evidence-supported option."
  require_literal "$system" 'select the simplest viable, most reversible choice.' "Low-risk reversible ties must resolve to the simplest viable option."
  require_literal "$system" 'safety, security, data integrity, compliance, unexpected cost, destructive or irreversible pre-production behavior, core-contract ambiguity, or subjective taste without evidence' "The complete recommendation pause taxonomy must be present."
  require_literal "$system" 'Hard platform blockers remain blockers.' "Hard platform blockers must not be converted into recommendations."
  require_literal "$system" 'A pause states the classification' "Recommendation pauses must identify their classification."
  require_literal "$system" 'choices, and a safe next action.' "Recommendation pauses must provide bounded choices and a safe next action."
  require_literal "$system" 'Decision, Evidence, Alternatives, Risk, Reversibility, Selection source, and Result/artifact' "Concise recommendation rationale fields must be explicit."
  require_literal "$system" 'Never include private chain-of-thought or transcript content.' "Recommendation rationale must exclude private reasoning and transcripts."
  require_literal "$system" 'continue automatically in the same session with recommendation mode retained and do not repeat the answered decision' "Required answers must resume recommendation mode without repeated decisions."
  require_literal "$system" 'Story 3 owns durable logging, execution state, reconciliation, and cross-session resumption.' "Story 2 must not claim Story 3 persistence mechanics."

  require_literal "$cursor_rule" 'Exactly one option label ends with the literal suffix `(Recommended)`.' "The Cursor rule mirror must include the recommendation label contract."
  require_literal "$cursor_rule" 'Story 3 owns durable logging, execution state, reconciliation, and cross-session resumption.' "The Cursor rule mirror must preserve the Story 2/3 boundary."

  for adapter in "$cursor_adapter" "$claude_adapter" "$codex_adapter"; do
    require_literal "$adapter" 'Preserve stable option identity across display, selection, rationale, and resume.' "Each adapter must preserve stable option identity."
    require_literal "$adapter" 'Adapters map interaction mechanics only; they do not choose recommendation policy.' "Each adapter must remain policy-neutral."
    require_literal "$adapter" 'Equivalent observable semantics are required: recommendation label or disclosed equivalence, classified pause, concise rationale, and same-session continuation after an answer.' "Each adapter must expose equivalent recommendation behavior."
  done
}

check_recommended_spec_implementation() {
  local preamble="$PROJECT_ROOT/commands/_preamble.md"
  local create_spec="$PROJECT_ROOT/commands/create-spec.md"
  local state_doc="$PROJECT_ROOT/.writ/docs/recommended-delivery-state-format.md"
  local helper="$PROJECT_ROOT/scripts/recommend-state.py"
  local recommendation_log="$PROJECT_ROOT/.writ/specs/2026-07-10-recommended-autonomous-delivery/recommendation-log.md"
  local scenario_output

  # ADR-013 (revised 2026-07-17): `--recommend` was redistributed to
  # `create-spec` (author + stop) and `implement-phase` (phase loop). The old
  # single-spec authoring->implement-spec->staging->production propagation is
  # deferred but preserved dormant. These static assertions therefore validate
  # only (a) create-spec's live two-command contract and (b) the dormant
  # state-format design doc. The retired implement-spec `--recommend`,
  # delivery_context propagation, and worktree-adoption assertions moved out;
  # the new phase-lane worktree model is covered by check_phase_lanes.
  scenario_output="$(mktemp)"
  python3 - "$create_spec" "$state_doc" > "$scenario_output" <<'PY'
import json
import re
import sys

create_path, state_path = sys.argv[1:]
create = open(create_path, encoding="utf-8").read()
state_doc = open(state_path, encoding="utf-8").read()

def emit(name, ok, reason):
    print(("STATIC_PASS" if ok else "STATIC_FAIL") + "\t" + name + "\t" + ("" if ok else reason))

def table_after(text, heading):
    start = text.find(heading)
    if start < 0:
        return {}
    rows = {}
    for line in text[start:].splitlines()[1:]:
        if line.startswith("### "):
            break
        if not line.startswith("|") or line.startswith("|---"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) >= 2 and cells[0] != "Invocation":
            rows[cells[0]] = cells[1]
    return rows

def fenced_after(text, anchor, language):
    start = text.find(anchor)
    if start < 0:
        raise ValueError(f"missing anchor {anchor}")
    match = re.search(rf"```{language}\n(.*?)\n```", text[start:], re.S)
    if not match:
        raise ValueError(f"missing {language} block after {anchor}")
    return match.group(1)

create_rows = table_after(create, "### Authoritative `--recommend` Invocation Matrix")

for invocation in (
    "`/create-spec --recommend [one-idea]`",
    "`/create-spec --recommend --from-issue <one-path>`",
    "`/create-spec --recommend --from-prototype`",
):
    emit("create-valid-" + invocation.strip("`").replace(" ", "_"), create_rows.get(invocation, "").startswith("Supported"), f"{invocation} is not a supported structured matrix row")

for invocation in (
    "`/create-spec --recommend --quick`",
    "`/create-spec --recommend --force`",
    "`--recommend` with multiple source modes",
    "`--recommend` with multiple issue paths or multiple free-form source arguments",
):
    outcome = create_rows.get(invocation, "")
    mutation_sentinel = not outcome.startswith("Reject")
    emit("create-reject-before-mutation-" + str(len(invocation)) + "-" + invocation.split()[0].strip("`/"), outcome.startswith("Reject") and not mutation_sentinel, f"{invocation} must reject before the mutation sentinel")

emit(
    "create-fail-before-mutation",
    0 <= create.find("Validate the complete invocation") < create.find("### Autonomous Authoring Boundary"),
    "create-spec invocation validation must precede the first recommended mutation phase",
)
emit(
    "create-terminal-scope",
    "never triggers `/implement-spec`" in create,
    "recommended authoring must stop before implementation and never trigger /implement-spec",
)
emit(
    "normal-mode-isolation",
    0 <= create.find("Normal branch (authoritative)") < create.find("### Authoritative `--recommend` Invocation Matrix"),
    "normal behavior must branch before recommended authoring",
)

try:
    state = json.loads(fenced_after(state_doc, "## `recommend-execution-v1`", "json"))
    emit("state-json-parses", True, "")
except Exception as exc:
    state = {}
    emit("state-json-parses", False, f"canonical state JSON does not parse: {exc}")

spec = state.get("spec", {})
manifest = spec.get("packageManifest", {})
artifacts = manifest.get("artifacts", []) if isinstance(manifest, dict) else []
manifest_paths = {item.get("path") for item in artifacts if isinstance(item, dict)}
required_artifact_section = state_doc[
    state_doc.find("Required artifacts are:"):state_doc.find("Additional sub-specs")
]
emit(
    "immutable-manifest-excludes-log",
    "recommendation-log.md" not in "\n".join(p or "" for p in manifest_paths)
    and "recommendation-log.md" not in required_artifact_section,
    "immutable package manifest must exclude the mutable recommendation log",
)
emit(
    "immutable-planning-projection",
    '"immutableProjectionSha256"' in fenced_after(state_doc, "## Package Manifest", "json")
    and "Mutable completion fields" in state_doc,
    "manifest identity must survive authorized story status/checklist/WWB progress changes",
)

log_state = spec.get("recommendationLog", {})
required_log_fields = {"path", "revision", "digestSha256", "entryIds", "pendingEntryIds"}
emit(
    "mutable-log-state-linkage",
    isinstance(log_state, dict) and required_log_fields <= set(log_state),
    f"state spec.recommendationLog is missing {sorted(required_log_fields - set(log_state) if isinstance(log_state, dict) else required_log_fields)}",
)
emit(
    "mutable-log-reconciliation",
    all(token in state_doc for token in ("append-only prefix", "pendingEntryIds", "unexpected rewrite")),
    "log append, pending-entry, and rewrite reconciliation rules are incomplete",
)

worktree_map = state.get("worktrees", {})
worktree = next(iter(worktree_map.values()), {}) if isinstance(worktree_map, dict) else {}
required_worktree_fields = {
    "storyId", "delegatedExecutionId", "ownershipToken", "path", "branchRef",
    "headSha", "activeStoryId", "activeGate", "startingSha", "currentSha",
    "status", "adoptionState", "adoptionEvidence", "mergeEvidence",
    "reservedAt", "updatedAt",
}
emit(
    "worktree-state-identity",
    isinstance(worktree, dict) and required_worktree_fields <= set(worktree),
    f"canonical keyed worktree record is missing {sorted(required_worktree_fields - set(worktree) if isinstance(worktree, dict) else required_worktree_fields)}",
)
PY

  while IFS=$'\t' read -r scenario_status scenario_name scenario_reason; do
    [ -z "$scenario_status" ] && continue
    CURRENT_STATIC_ASSERTIONS=$((CURRENT_STATIC_ASSERTIONS + 1))
    if [ "$scenario_status" = "STATIC_PASS" ]; then
      CURRENT_STATIC_ASSERTIONS_PASSED=$((CURRENT_STATIC_ASSERTIONS_PASSED + 1))
    else
      add_finding "static:$scenario_name" "$scenario_reason" "Repair the supplementary static Story 3 contract assertion."
    fi
  done < "$scenario_output"
  rm -f "$scenario_output"

  scenario_output="$(mktemp)"
  python3 - "$helper" > "$scenario_output" <<'PY'
import copy
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

helper = pathlib.Path(sys.argv[1]).resolve()
workspace = pathlib.Path(tempfile.mkdtemp(prefix="writ-story3-eval-"))
scenario_total = 0

def emit(name, ok, reason=""):
    global scenario_total
    scenario_total += 1
    safe_reason = "" if ok else str(reason).replace("\t", " ").replace("\r", " ").replace("\n", "\\n")
    print(("PASS" if ok else "FAIL") + "\t" + name + "\t" + safe_reason)

def beat(msg):
    # Progress heartbeat to stderr so a slow run is visibly progressing.
    # stdout is reserved for scenario TSV, so this never pollutes parsing.
    print(f"[recommended-spec-impl] {msg}", file=sys.stderr, flush=True)

def command(args, cwd=None, check=True):
    result = subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and result.returncode:
        raise RuntimeError(f"{args}: {result.stderr or result.stdout}")
    return result

def helper_run(*args, check=True):
    result = command([sys.executable, str(helper), *map(str, args)], check=False)
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        payload = {"invalid_output": result.stdout, "stderr": result.stderr}
    if check and result.returncode:
        raise RuntimeError(f"helper failed: {payload}")
    return result, payload

def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

_fixture_template = None

def _build_fixture_template():
    # Build the git-backed fixture repo exactly once, then copytree it per
    # fixture() call. Fixtures are byte-identical, so this trades ~5 git spawns
    # per call for a single filesystem copy — the dominant repeated-spawn cost.
    beat("building fixture template (one-time git repo)")
    repo = workspace / "_fixture-template" / "repo"
    repo.mkdir(parents=True)
    command(["git", "init", "-b", "main"], cwd=repo)
    command(["git", "config", "user.name", "Writ Eval"], cwd=repo)
    command(["git", "config", "user.email", "eval@example.invalid"], cwd=repo)
    spec = repo / ".writ/specs/2026-07-10-fixture"
    write(spec / "spec.md", "# Fixture\n\n> **Status:** Not Started\n> **Contract Locked:** ✅\n\n## Contract\nLocked.\n")
    write(spec / "spec-lite.md", "# Fixture Lite\n\nLocked planning summary.\n")
    write(spec / "sub-specs/technical-spec.md", "# Technical\n\nNo unresolved operations.\n")
    story_template = """# Story {number}: Fixture

> **Status:** Not Started
> **Dependencies:** {dependencies}

## Acceptance Criteria
- [ ] Given input one, when handled, then result one.
- [ ] Given input two, when handled, then result two.
- [ ] Given input three, when handled, then result three.

## Implementation Tasks
- [ ] {number}.1 First task
- [ ] {number}.2 Second task
- [ ] {number}.3 Third task
- [ ] {number}.4 Fourth task
- [ ] {number}.5 Fifth task
"""
    write(spec / "user-stories/story-1-one.md", story_template.format(number=1, dependencies="None"))
    write(spec / "user-stories/story-2-two.md", story_template.format(number=2, dependencies="Story 1"))
    write(spec / "user-stories/README.md", """# Stories

> **Progress:** 0/2

| Story | Title | Status | Priority | Dependencies | Tasks | Progress |
|---|---|---|---|---|---:|---:|
| [1](story-1-one.md) | One | Not Started | High | None | 5 | 0/5 |
| [2](story-2-two.md) | Two | Not Started | High | Story 1 | 5 | 0/5 |
""")
    write(spec / "recommendation-log.md", """# Recommendation Log: Fixture

> **Spec:** `.writ/specs/2026-07-10-fixture/spec.md`
> **Purpose:** Eval
> **Privacy:** Decisions only

## REC-001 — 2026-07-10T15:00:00Z — planning

- **Decision:** Use fixture.
- **Evidence:** Locked files.
- **Alternatives:** Stop.
- **Risk:** Low.
- **Reversibility:** High.
- **Selection:** Automatic.
- **Result:** Applied — fixture.
""")
    command(["git", "add", "."], cwd=repo)
    command(["git", "commit", "-m", "fixture"], cwd=repo)
    return repo


def fixture(name):
    global _fixture_template
    if _fixture_template is None:
        _fixture_template = _build_fixture_template()
    repo = workspace / name / "repo"
    repo.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(_fixture_template, repo)
    return repo, pathlib.Path(".writ/specs/2026-07-10-fixture")

def start(repo, spec, suffix, entry="implement-spec", invocation=None):
    state = repo / f".writ/state/recommend-execution-{suffix}.json"
    invocation = invocation or ["--recommend", spec.name]
    result, payload = helper_run(
        "start", "--repo", repo, "--spec", spec, "--state", state,
        "--execution-id", suffix, "--token", f"token-{suffix}",
        "--entry-command", entry, "--invocation-json", json.dumps(invocation),
        check=False,
    )
    return state, result, payload

def reserve(repo, state, story, delegated, token, path, branch_ref, head):
    launch = repo / f".writ/state/launch-{story}-{delegated}.json"
    write(launch, json.dumps({
        "schema": "recommend-worktree-launch-v1",
        "execution_id": json.loads(state.read_text())["executionId"],
        "story_id": story,
        "delegated_execution_id": delegated,
        "ownership_token": token,
        "path": str(path),
        "branch_ref": branch_ref,
        "head_sha": head,
        "starting_sha": head,
        "active_gate": "launch",
        "mode": "linked_worktree",
    }))
    return helper_run(
        "reserve-worktree", "--state", state, "--repo", repo,
        "--launch-result", launch, check=False,
    )

def bind_success_result(state, story):
    value = json.loads(state.read_text())
    value["storyExecution"]["storyResults"][story] = {
        "schema": "recommend-command-result-v1",
        "execution_id": value["executionId"],
        "mode": "recommend",
        "command": "implement-story",
        "status": "succeeded",
        "completed_state": None,
        "resume_state": None,
        "evidence": {"summary": "Story gates passed.", "artifacts": []},
        "identifiers": {"story_id": story},
        "required_answer": {
            "decision_id": None, "question_id": None, "option_ids": [],
            "selected_option_id": None, "resume_transition": None, "interaction_id": None,
        },
        "blocker": {"code": None, "summary": None},
    }
    state.write_text(json.dumps(value), encoding="utf-8")

def owned_worktree(name):
    repo, spec = fixture(name)
    state, _, _ = start(repo, spec, name)
    head = command(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip()
    path = workspace / name / "delegated"
    branch = f"{name}-story-1"
    command(["git", "worktree", "add", "-b", branch, str(path), head], cwd=repo)
    _, payload = reserve(repo, state, "story-1", "delegate-1", "owner-1", path, f"refs/heads/{branch}", head)
    bind_success_result(state, "story-1")
    return repo, state, path, branch, payload["worktree_key"]

try:
    repo, spec = fixture("propagation")
    state, result, payload = start(repo, spec, "create", "create-spec", ["--recommend", "fixture"])
    context = payload.get("delivery_context", {})
    context_file = repo / "context.json"
    write(context_file, json.dumps(context))
    context_result, context_payload = helper_run("validate-context", "--state", state, "--context", context_file, check=False)
    emit("create-to-implement-context", result.returncode == 0 and context_result.returncode == 0 and context_payload.get("status") == "valid", str(context_payload))
    bad_context = dict(context, propagation_token="wrong-token")
    write(context_file, json.dumps(bad_context))
    bad_result, bad_payload = helper_run("validate-context", "--state", state, "--context", context_file, check=False)
    emit("mismatched-context-blocks", bad_result.returncode != 0 and bad_payload.get("blocker", {}).get("code") == "delivery_context_mismatch", str(bad_payload))

    repo, spec = fixture("direct")
    state, result, payload = start(repo, spec, "direct")
    emit("direct-existing-spec-entry", result.returncode == 0 and state.exists() and payload.get("delivery_context", {}).get("parent_command") == "implement-spec", str(payload))

    invalid = [
        ("create-quick", "create-spec", ["--recommend", "--quick"]),
        ("create-force", "create-spec", ["--recommend", "--force"]),
        ("create-dry-run", "create-spec", ["--recommend", "--dry-run"]),
        ("create-draft", "create-spec", ["--recommend", "--draft"]),
        ("create-no-split", "create-spec", ["--recommend", "--no-split"]),
        ("create-skip-gate", "create-spec", ["--recommend", "--skip-gate"]),
        ("create-no-tag", "create-spec", ["--recommend", "--no-tag"]),
        ("create-sources", "create-spec", ["--recommend", "--from-issue", "--from-prototype", "issue.md"]),
        ("create-issues", "create-spec", ["--recommend", "--from-issue", "one.md", "two.md"]),
        ("create-resume", "create-spec", ["--recommend", "--resume"]),
        ("implement-quick", "implement-spec", ["--recommend", "--quick"]),
        ("implement-force", "implement-spec", ["--recommend", "--force"]),
        ("implement-dry-run", "implement-spec", ["--recommend", "--dry-run"]),
        ("implement-draft", "implement-spec", ["--recommend", "--draft"]),
        ("implement-no-split", "implement-spec", ["--recommend", "--no-split"]),
        ("implement-skip-gate", "implement-spec", ["--recommend", "--skip-gate"]),
        ("implement-no-tag", "implement-spec", ["--recommend", "--no-tag"]),
        ("implement-from", "implement-spec", ["--recommend", "--from", "story-2"]),
        ("implement-resume", "implement-spec", ["--recommend", "--resume"]),
        ("implement-multiple", "implement-spec", ["--recommend", "one", "two"]),
        ("phase", "implement-phase", ["--recommend", spec.name]),
    ]
    for name, entry, invocation in invalid:
        candidate = repo / f".writ/state/{name}.json"
        sentinel = repo / f".writ/state/{name}.mutated"
        result, _ = helper_run(
            "start", "--repo", repo, "--spec", spec, "--state", candidate,
            "--execution-id", name, "--token", f"token-{name}",
            "--entry-command", entry, "--invocation-json", json.dumps(invocation),
            check=False,
        )
        if result.returncode == 0:
            sentinel.parent.mkdir(parents=True, exist_ok=True)
            sentinel.touch()
        emit(f"invalid-{name}-no-mutation", result.returncode != 0 and not candidate.exists() and not sentinel.exists(), result.stdout)

    normal_state = repo / ".writ/state/normal.json"
    recommended_revision_before = json.loads(state.read_text())["revision"]
    result, payload = helper_run(
        "start", "--repo", repo, "--spec", "missing-spec", "--state", normal_state,
        "--execution-id", "normal", "--token", "normal-token",
        "--entry-command", "implement-spec", "--invocation-json", json.dumps([spec.name]),
        check=False,
    )
    recommended_revision_after = json.loads(state.read_text())["revision"]
    emit("normal-mode-no-create-or-reconcile", result.returncode == 0 and payload.get("action") == "no_recommended_state" and not normal_state.exists() and recommended_revision_after == recommended_revision_before, str(payload))

    repo, spec = fixture("immutable")
    state, result, _ = start(repo, spec, "immutable")
    emit("complete-package-validates", result.returncode == 0 and state.exists(), result.stdout)
    with (repo / spec / "sub-specs/technical-spec.md").open("a", encoding="utf-8") as handle:
        handle.write("\nchanged immutable requirement\n")
    result, payload = helper_run("reconcile", "--state", state, "--repo", repo, check=False)
    emit("changed-immutable-artifact-blocks", result.returncode != 0 and payload.get("blocker", {}).get("code") == "package_manifest_mismatch", str(payload))

    repo, spec = fixture("authorized-progress")
    state, _, _ = start(repo, spec, "authorized-progress")
    story = repo / spec / "user-stories/story-1-one.md"
    story_text = story.read_text().replace("> **Status:** Not Started", "> **Status:** Completed ✅")
    story_text = story_text.replace("- [ ]", "- [x]") + "\n## What Was Built\n\nAuthorized implementation record.\n"
    write(story, story_text)
    readme = repo / spec / "user-stories/README.md"
    readme_text = readme.read_text().replace("> **Progress:** 0/2", "> **Progress:** 1/2")
    readme_text = readme_text.replace(
        "| [1](story-1-one.md) | One | Not Started | High | None | 5 | 0/5 |",
        "| [1](story-1-one.md) | One | Completed ✅ | High | None | 5 | 5/5 |",
    )
    write(readme, readme_text)
    result, payload = helper_run("reconcile", "--state", state, "--repo", repo, check=False)
    emit("authorized-progress-preserves-immutable-identity", result.returncode == 0, str(payload))

    for name, mutate, expected in (
        ("contract-lock", lambda root, s: write(root / s / "spec.md", (root / s / "spec.md").read_text().replace("> **Contract Locked:** ✅\n", "")), "contract_unlocked"),
        ("required-artifact", lambda root, s: (root / s / "spec-lite.md").unlink(), "incomplete_package"),
        ("indexed-story-missing", lambda root, s: (root / s / "user-stories/story-2-two.md").unlink(), "incomplete_package"),
        ("unindexed-story", lambda root, s: write(root / s / "user-stories/story-3-extra.md", (root / s / "user-stories/story-1-one.md").read_text().replace("Story 1", "Story 3").replace("1.", "3.")), "readme_mismatch"),
        ("status-agreement", lambda root, s: write(root / s / "user-stories/README.md", (root / s / "user-stories/README.md").read_text().replace("| One | Not Started |", "| One | In Progress |")), "readme_mismatch"),
        ("task-total", lambda root, s: write(root / s / "user-stories/README.md", (root / s / "user-stories/README.md").read_text().replace("| None | 5 | 0/5 |", "| None | 6 | 0/6 |")), "readme_mismatch"),
        ("completed-count", lambda root, s: write(root / s / "user-stories/README.md", (root / s / "user-stories/README.md").read_text().replace("| None | 5 | 0/5 |", "| None | 5 | 1/5 |")), "readme_mismatch"),
        ("overall-progress", lambda root, s: write(root / s / "user-stories/README.md", (root / s / "user-stories/README.md").read_text().replace("> **Progress:** 0/2", "> **Progress:** 1/2")), "readme_mismatch"),
        ("acceptance-count", lambda root, s: write(root / s / "user-stories/story-1-one.md", (root / s / "user-stories/story-1-one.md").read_text().replace("- [ ] Given input three, when handled, then result three.\n", "")), "invalid_story"),
        ("task-count", lambda root, s: write(root / s / "user-stories/story-1-one.md", (root / s / "user-stories/story-1-one.md").read_text().replace("- [ ] 1.5 Fifth task\n", "")), "invalid_story"),
        ("unplanned", lambda root, s: write(root / s / "sub-specs/technical-spec.md", "# Technical\n\n[UNPLANNED]\n"), "unplanned_operation"),
        ("referenced-subspec", lambda root, s: write(root / s / "spec.md", (root / s / "spec.md").read_text() + "\n[Missing](sub-specs/missing.md)\n"), "incomplete_package"),
    ):
        repo, spec = fixture("package-" + name)
        mutate(repo, spec)
        _, result, payload = start(repo, spec, "package-" + name)
        emit("package-rejects-" + name, result.returncode != 0 and payload.get("blocker", {}).get("code") == expected, str(payload))

    for name, old, new in (
        ("semantic-task", "First task", "Semantically changed task"),
        ("semantic-ac", "result one.", "changed contractual result."),
    ):
        repo, spec = fixture("package-" + name)
        state, _, _ = start(repo, spec, "package-" + name)
        story = repo / spec / "user-stories/story-1-one.md"
        write(story, story.read_text().replace(old, new))
        result, payload = helper_run("reconcile", "--state", state, "--repo", repo, check=False)
        emit("package-rejects-" + name, result.returncode != 0 and payload.get("blocker", {}).get("code") == "package_manifest_mismatch", str(payload))

    repo, spec = fixture("package-dag")
    story1 = repo / spec / "user-stories/story-1-one.md"
    write(story1, story1.read_text().replace("> **Dependencies:** None", "> **Dependencies:** Story 2"))
    readme = repo / spec / "user-stories/README.md"
    write(readme, readme.read_text().replace("| One | Not Started | High | None |", "| One | Not Started | High | Story 2 |"))
    _, result, payload = start(repo, spec, "package-dag")
    emit("package-rejects-dependency-cycle", result.returncode != 0 and payload.get("blocker", {}).get("code") == "invalid_dag", str(payload))

    repo, spec = fixture("package-referenced-positive")
    extra = repo / spec / "sub-specs/extra.md"
    write(extra, "# Referenced Sub-Spec\n\nStable requirement.\n")
    spec_file = repo / spec / "spec.md"
    write(spec_file, spec_file.read_text() + "\n[Extra](sub-specs/extra.md)\n")
    _, result, payload = start(repo, spec, "package-referenced-positive")
    created = json.loads((repo / ".writ/state/recommend-execution-package-referenced-positive.json").read_text()) if result.returncode == 0 else {}
    paths = [item["path"] for item in created.get("spec", {}).get("packageManifest", {}).get("artifacts", [])]
    emit("package-discovers-referenced-subspec", result.returncode == 0 and any(path.endswith("/sub-specs/extra.md") for path in paths), str(payload))

    repo, spec = fixture("log-append")
    state, _, _ = start(repo, spec, "log-append")
    with (repo / spec / "recommendation-log.md").open("a", encoding="utf-8") as handle:
        handle.write("""
## REC-002 — 2026-07-10T15:01:00Z — implementing

- **Decision:** Continue.
- **Evidence:** State valid.
- **Alternatives:** Stop.
- **Risk:** Low.
- **Reversibility:** High.
- **Selection:** Reconciliation.
- **Result:** Applied — continued.
""")
    result, payload = helper_run("reconcile", "--state", state, "--repo", repo, check=False)
    updated = json.loads(state.read_text())
    emit("append-only-log-advances", result.returncode == 0 and updated["spec"]["recommendationLog"]["revision"] == 2 and updated["spec"]["recommendationLog"]["entryIds"][-1] == "REC-002", str(payload))

    repo, spec = fixture("log-rewrite")
    state, _, _ = start(repo, spec, "log-rewrite")
    log_path = repo / spec / "recommendation-log.md"
    log_path.write_text(log_path.read_text().replace("Use fixture.", "Rewrite fixture."), encoding="utf-8")
    result, payload = helper_run("reconcile", "--state", state, "--repo", repo, check=False)
    emit("rewritten-log-entry-blocks", result.returncode != 0 and payload.get("blocker", {}).get("code") == "recommendation_log_contradiction", str(payload))

    repo, spec = fixture("log-pending")
    log_path = repo / spec / "recommendation-log.md"
    log_path.write_text(log_path.read_text().replace("Applied — fixture.", "Pending — operation fixture."), encoding="utf-8")
    state, start_result, _ = start(repo, spec, "log-pending")
    log_path.write_text(log_path.read_text().replace("Pending — operation fixture.", "Applied — reconciled fixture."), encoding="utf-8")
    result, payload = helper_run("reconcile", "--state", state, "--repo", repo, check=False)
    updated = json.loads(state.read_text())
    emit("pending-log-result-finalizes", start_result.returncode == 0 and result.returncode == 0 and updated["spec"]["recommendationLog"]["revision"] == 2 and not updated["spec"]["recommendationLog"]["pendingEntryIds"], str(payload))

    repo, spec = fixture("parallel")
    story2 = repo / spec / "user-stories/story-2-two.md"
    write(story2, story2.read_text().replace("> **Dependencies:** Story 1", "> **Dependencies:** None"))
    index = repo / spec / "user-stories/README.md"
    write(index, index.read_text().replace("| Two | Not Started | High | Story 1 |", "| Two | Not Started | High | None |"))
    state, _, _ = start(repo, spec, "parallel")
    head = command(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip()
    worktrees = []
    handshake_evidence = []
    for story in ("story-1", "story-2"):
        path = workspace / "parallel" / story
        branch = f"wt-{story}"
        command(["git", "worktree", "add", "-b", branch, str(path), head], cwd=repo)
        gate1_marker = path / "gate1-edit.txt"
        no_edit_before_ack = not gate1_marker.exists()
        result, payload = reserve(
            repo, state, story, f"delegate-{story}", f"owner-{story}",
            path, f"refs/heads/{branch}", head,
        )
        persisted = json.loads(state.read_text())
        key = payload.get("worktree_key")
        persisted_before_edit = result.returncode == 0 and payload.get("schema") == "recommend-worktree-reservation-ack-v1" and key in persisted["worktrees"]
        if persisted_before_edit:
            write(gate1_marker, "edit allowed after durable acknowledgment\n")
        handshake_evidence.append(no_edit_before_ack and persisted_before_edit and gate1_marker.exists())
        worktrees.append((story, path, result, payload))
    persisted = json.loads(state.read_text())
    plan = {"batches": [{"parallel": True, "stories": ["story-1", "story-2"]}]}
    nested = repo / ".writ/state/execution-parallel.json"
    write(nested, json.dumps({
        "spec": persisted["spec"]["id"],
        "plan": plan,
        "stories": {
            "story-1": {"status": "in_progress", "phase": "coding"},
            "story-2": {"status": "in_progress", "phase": "coding"},
        },
    }))
    persisted["storyExecution"]["executionStatePath"] = nested.relative_to(repo).as_posix()
    persisted["storyExecution"]["planDigest"] = __import__("hashlib").sha256(
        json.dumps(plan, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    persisted["storyExecution"]["activeStoryIds"] = ["story-1", "story-2"]
    state.write_text(json.dumps(persisted), encoding="utf-8")
    result, payload = helper_run("reconcile", "--state", state, "--repo", repo, check=False)
    updated = json.loads(state.read_text())
    adopted = len(updated["worktrees"]) == 2 and all(record["adoptionState"] == "adopted" for record in updated["worktrees"].values())
    for story, path, _, payload in worktrees:
        command(["git", "add", "gate1-edit.txt"], cwd=path)
        command(["git", "commit", "-m", f"implement {story}"], cwd=path)
        command(["git", "merge", "--no-ff", "-m", f"integrate {story}", f"wt-{story}"], cwd=repo)
        bind_success_result(state, story)
    completion_results = [
        helper_run("complete-worktree", "--state", state, "--repo", repo, "--worktree-key", key, check=False)[0]
        for key in sorted(updated["worktrees"])
    ]
    completed = json.loads(state.read_text())
    emit("launch-ack-precedes-gate1-mutation", all(handshake_evidence), str([item[3] for item in worktrees]))
    emit("parallel-worktrees-reserved-adopted-integrated", all(item[2].returncode == 0 for item in worktrees) and result.returncode == 0 and adopted and all(item.returncode == 0 for item in completion_results) and all(record["status"] == "integrated" and record["mergeEvidence"].get("status") == "integrated" for record in completed["worktrees"].values()), str(payload))

    repo, spec = fixture("ambiguous")
    state, _, _ = start(repo, spec, "ambiguous")
    head = command(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip()
    path = workspace / "ambiguous" / "story-1"
    command(["git", "worktree", "add", "-b", "ambiguous-story-1", str(path), head], cwd=repo)
    reserve(repo, state, "story-1", "delegate-1", "owner-1", path, "refs/heads/ambiguous-story-1", head)
    value = json.loads(state.read_text())
    duplicate = copy.deepcopy(next(iter(value["worktrees"].values())))
    duplicate["delegatedExecutionId"] = "delegate-2"
    duplicate["ownershipToken"] = "owner-2"
    value["worktrees"]["story-1::delegate-2::owner-2"] = duplicate
    state.write_text(json.dumps(value), encoding="utf-8")
    result, payload = helper_run("reconcile", "--state", state, "--repo", repo, check=False)
    emit("ambiguous-worktree-ownership-blocks", result.returncode != 0 and payload.get("blocker", {}).get("code") == "worktree_ownership_ambiguous", str(payload))

    repo, spec = fixture("stale")
    state, _, _ = start(repo, spec, "stale")
    head = command(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip()
    path = workspace / "stale" / "story-1"
    command(["git", "worktree", "add", "-b", "stale-story-1", str(path), head], cwd=repo)
    reserve(repo, state, "story-1", "delegate-1", "owner-1", path, "refs/heads/stale-story-1", head)
    write(path / "changed.txt", "changed\n")
    command(["git", "add", "changed.txt"], cwd=path)
    command(["git", "commit", "-m", "advance"], cwd=path)
    result, payload = helper_run("reconcile", "--state", state, "--repo", repo, check=False)
    emit("stale-worktree-head-blocks", result.returncode != 0 and payload.get("blocker", {}).get("code") == "worktree_identity_stale", str(payload))

    repo, spec = fixture("stranded")
    state, _, _ = start(repo, spec, "stranded")
    head = command(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip()
    path = workspace / "stranded" / "story-1"
    command(["git", "worktree", "add", "-b", "stranded-story-1", str(path), head], cwd=repo)
    reserve(repo, state, "story-1", "delegate-1", "owner-1", path, "refs/heads/stranded-story-1", head)
    command(["git", "worktree", "remove", "--force", str(path)], cwd=repo)
    result, payload = helper_run("reconcile", "--state", state, "--repo", repo, check=False)
    emit("stranded-worktree-blocks", result.returncode != 0 and payload.get("blocker", {}).get("code") == "stranded_worktree_missing", str(payload))

    repo, state, path, branch, key = owned_worktree("completion-dirty")
    write(path / "dirty.txt", "uncommitted\n")
    result, payload = helper_run("complete-worktree", "--state", state, "--repo", repo, "--worktree-key", key, check=False)
    emit("dirty-worktree-completion-blocks", result.returncode != 0 and payload.get("blocker", {}).get("code") == "worktree_dirty", str(payload))

    repo, state, path, branch, key = owned_worktree("completion-not-integrated")
    write(path / "story-change.txt", "committed story content\n")
    command(["git", "add", "story-change.txt"], cwd=path)
    command(["git", "commit", "-m", "implement story"], cwd=path)
    result, payload = helper_run("complete-worktree", "--state", state, "--repo", repo, "--worktree-key", key, check=False)
    emit("committed-not-integrated-blocks", result.returncode != 0 and payload.get("blocker", {}).get("code") == "worktree_not_integrated", str(payload))

    repo, state, path, branch, key = owned_worktree("completion-integrated")
    write(path / "story-change.txt", "committed story content\n")
    command(["git", "add", "story-change.txt"], cwd=path)
    command(["git", "commit", "-m", "implement story"], cwd=path)
    source_head = command(["git", "rev-parse", "HEAD"], cwd=path).stdout.strip()
    command(["git", "merge", "--no-ff", "-m", "integrate story", branch], cwd=repo)
    target_head = command(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip()
    result, payload = helper_run("complete-worktree", "--state", state, "--repo", repo, "--worktree-key", key, check=False)
    completed = json.loads(state.read_text())["worktrees"][key]
    emit(
        "integrated-worktree-releases-ownership",
        result.returncode == 0
        and completed["status"] == "integrated"
        and completed["mergeEvidence"]["sourceHeadSha"] == source_head
        and completed["mergeEvidence"]["targetHeadSha"] == target_head,
        str(payload),
    )

    repo, state, path, branch, key = owned_worktree("completion-ambiguous")
    write(path / "story-change.txt", "committed story content\n")
    command(["git", "add", "story-change.txt"], cwd=path)
    command(["git", "commit", "-m", "implement story"], cwd=path)
    command(["git", "merge", "--no-ff", "-m", "integrate story", branch], cwd=repo)
    command(["git", "checkout", "-b", "unexpected-target"], cwd=repo)
    result, payload = helper_run("complete-worktree", "--state", state, "--repo", repo, "--worktree-key", key, check=False)
    emit("ambiguous-target-completion-blocks", result.returncode != 0 and payload.get("blocker", {}).get("code") == "worktree_target_ambiguous", str(payload))

    repo, state, path, branch, key = owned_worktree("completion-stale")
    write(path / "story-change.txt", "committed story content\n")
    command(["git", "add", "story-change.txt"], cwd=path)
    command(["git", "commit", "-m", "implement story"], cwd=path)
    stale = json.loads(state.read_text())
    stale["worktrees"][key]["startingSha"] = "0" * 40
    state.write_text(json.dumps(stale), encoding="utf-8")
    result, payload = helper_run("complete-worktree", "--state", state, "--repo", repo, "--worktree-key", key, check=False)
    emit("stale-completion-evidence-blocks", result.returncode != 0 and payload.get("status") == "blocked", str(payload))

    empty_answer = {
        "decision_id": None, "question_id": None, "option_ids": [],
        "selected_option_id": None, "resume_transition": None, "interaction_id": None,
    }
    result_base = {
        "schema": "recommend-command-result-v1", "execution_id": "exec", "mode": "recommend",
        "command": "implement-story", "completed_state": None, "resume_state": "implementing",
        "evidence": {"summary": "fixture evidence", "artifacts": []}, "identifiers": {},
        "required_answer": empty_answer, "blocker": {"code": None, "summary": None},
    }
    failed = workspace / "failed.json"
    write(failed, json.dumps({**result_base, "status": "failed"}))
    result, payload = helper_run("normalize-result", "--input", failed, "--execution-id", "exec", check=False)
    emit("failed-result-normalizes-blocked", result.returncode == 0 and payload.get("status") == "blocked" and payload.get("blocker", {}).get("code"), str(payload))

    answer = workspace / "answer.json"
    required_answer = {
        "decision_id": "DEC-1", "question_id": "Q-1", "option_ids": ["yes", "no"],
        "selected_option_id": None, "resume_transition": "implementing", "interaction_id": "I-1",
    }
    write(answer, json.dumps({
        **result_base, "status": "answer_required", "required_answer": required_answer,
    }))
    result, payload = helper_run("normalize-result", "--input", answer, "--execution-id", "exec", check=False)
    emit("required-answer-identity-preserved", result.returncode == 0 and payload.get("required_answer") == required_answer, str(payload))

    for name, mutate, expected in (
        ("missing-top-key", lambda value: value.pop("repository"), "invalid_state"),
        ("invalid-status-enum", lambda value: value.update(status="done"), "invalid_state"),
        ("invalid-revision-type", lambda value: value.update(revision="1"), "invalid_revision"),
        ("unsupported-major", lambda value: value.update(schema="recommend-execution-v2", schemaVersion=2), "unsupported_schema"),
        ("invalid-manifest", lambda value: value["spec"]["packageManifest"]["artifacts"][0].update(immutableProjectionSha256="bad"), "invalid_state"),
        ("invalid-log-shape", lambda value: value["spec"]["recommendationLog"].pop("entryDigests"), "invalid_state"),
        ("reserved-delivery-field", lambda value: value["delivery"].update(pr={"number": 1}), "invalid_state"),
        ("invalid-transition", lambda value: value["transitions"].append({"sequence": 4}), "invalid_state"),
    ):
        repo, spec = fixture("state-" + name)
        state, _, _ = start(repo, spec, "state-" + name)
        value = json.loads(state.read_text())
        mutate(value)
        state.write_text(json.dumps(value), encoding="utf-8")
        result, payload = helper_run("reconcile", "--state", state, "--repo", repo, check=False)
        emit("state-rejects-" + name, result.returncode != 0 and payload.get("blocker", {}).get("code") == expected, str(payload))

    repo, spec = fixture("state-unknown-compatible")
    state, _, _ = start(repo, spec, "state-unknown-compatible")
    value = json.loads(state.read_text())
    value["compatibleExtension"] = {"preserve": True}
    value["repository"]["compatibleNestedExtension"] = "kept"
    state.write_text(json.dumps(value), encoding="utf-8")
    result, payload = helper_run("reconcile", "--state", state, "--repo", repo, check=False)
    preserved = json.loads(state.read_text())
    emit(
        "state-preserves-compatible-unknown-fields",
        result.returncode == 0
        and preserved.get("compatibleExtension") == {"preserve": True}
        and preserved["repository"].get("compatibleNestedExtension") == "kept",
        str(payload),
    )

    repo, state, path, branch, key = owned_worktree("state-invalid-worktree")
    value = json.loads(state.read_text())
    value["worktrees"][key].pop("ownershipToken")
    state.write_text(json.dumps(value), encoding="utf-8")
    result, payload = helper_run("reconcile", "--state", state, "--repo", repo, check=False)
    emit("state-rejects-malformed-worktree", result.returncode != 0 and payload.get("blocker", {}).get("code") == "invalid_state", str(payload))

    malformed_result = workspace / "malformed-result.json"
    write(malformed_result, json.dumps({"schema": "recommend-command-result-v1", "status": "succeeded"}))
    result, payload = helper_run("normalize-result", "--input", malformed_result, "--execution-id", "exec", check=False)
    emit("malformed-result-fails-closed", result.returncode != 0 and payload.get("blocker", {}).get("code") == "invalid_result", str(payload))

    unknown_result = workspace / "unknown-result.json"
    write(unknown_result, json.dumps({**result_base, "status": "mystery"}))
    result, payload = helper_run("normalize-result", "--input", unknown_result, "--execution-id", "exec", check=False)
    emit("unknown-result-status-fails-closed", result.returncode != 0 and payload.get("blocker", {}).get("code") == "invalid_result", str(payload))

    for name, bad_answer in (
        ("null-decision", {**required_answer, "decision_id": None}),
        ("empty-question", {**required_answer, "question_id": ""}),
        ("duplicate-options", {**required_answer, "option_ids": ["yes", "yes"]}),
        ("empty-option", {**required_answer, "option_ids": ["yes", ""]}),
    ):
        candidate = workspace / f"answer-{name}.json"
        write(candidate, json.dumps({**result_base, "status": "answer_required", "required_answer": bad_answer}))
        result, payload = helper_run("normalize-result", "--input", candidate, "--execution-id", "exec", check=False)
        emit("answer-required-rejects-" + name, result.returncode != 0 and payload.get("blocker", {}).get("code") == "invalid_required_answer", str(payload))

    result, payload = helper_run("reconcile", "--state", workspace / "missing-state.json", "--repo", workspace, check=False)
    emit("operational-exception-is-blocked-json", result.returncode != 0 and payload.get("status") == "blocked" and payload.get("blocker", {}).get("code"), str(payload))

    project = helper.parent.parent
    beat("sandbox: building source repo (one-time)")
    source = workspace / "update-source"
    shutil.copytree(
        project,
        source,
        ignore=shutil.ignore_patterns(".git", ".cursor", ".claude", ".codex", ".writ", "__pycache__"),
    )
    (source / ".writ/docs").mkdir(parents=True)
    shutil.copy2(
        project / ".writ/docs/recommended-delivery-state-format.md",
        source / ".writ/docs/recommended-delivery-state-format.md",
    )
    command(["git", "init", "-b", "main"], cwd=source)
    command(["git", "config", "user.name", "Writ Eval"], cwd=source)
    command(["git", "config", "user.email", "eval@example.invalid"], cwd=source)
    command(["git", "add", "."], cwd=source)
    command(["git", "commit", "-m", "sandbox source"], cwd=source)

    for platform in ("cursor", "claude", "codex"):
        beat(f"sandbox: {platform} (install/update/unlink)")
        target = workspace / f"install-{platform}"
        target.mkdir()
        dry = command(
            ["bash", str(project / "scripts/install.sh"), "--platform", platform, "--dry-run", "--no-commit"],
            cwd=target, check=False,
        )
        helper_dest = target / "scripts/recommend-state.py"
        state_doc_dest = target / ".writ/docs/recommended-delivery-state-format.md"
        emit(
            f"install-{platform}-dry-run-helper",
            dry.returncode == 0 and "scripts/recommend-state.py" in dry.stdout and not helper_dest.exists(),
            dry.stdout + dry.stderr,
        )
        emit(
            f"install-{platform}-dry-run-state-doc",
            dry.returncode == 0
            and ".writ/docs/recommended-delivery-state-format.md" in dry.stdout
            and not state_doc_dest.exists(),
            dry.stdout + dry.stderr,
        )
        installed = command(
            ["bash", str(project / "scripts/install.sh"), "--platform", platform, "--no-commit"],
            cwd=target, check=False,
        )
        invoked = command([sys.executable, str(helper_dest), "--help"], cwd=target, check=False) if helper_dest.exists() else installed
        emit(
            f"install-{platform}-helper-executable",
            installed.returncode == 0 and helper_dest.is_file() and invoked.returncode == 0,
            installed.stdout + installed.stderr,
        )
        emit(
            f"install-{platform}-state-doc",
            installed.returncode == 0
            and state_doc_dest.is_file()
            and state_doc_dest.read_bytes() == (project / ".writ/docs/recommended-delivery-state-format.md").read_bytes(),
            installed.stdout + installed.stderr,
        )
        helper_dest.unlink()
        state_doc_dest.unlink()
        env = dict(os.environ, WRIT_REPO=str(source))
        update_dry = subprocess.run(
            ["bash", str(project / "scripts/update.sh"), "--platform", platform, "--dry-run", "--no-commit"],
            cwd=target, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        emit(
            f"update-{platform}-dry-run-helper",
            update_dry.returncode == 0 and "scripts/recommend-state.py" in update_dry.stdout and not helper_dest.exists(),
            update_dry.stdout + update_dry.stderr,
        )
        emit(
            f"update-{platform}-dry-run-state-doc",
            update_dry.returncode == 0
            and ".writ/docs/recommended-delivery-state-format.md" in update_dry.stdout
            and not state_doc_dest.exists(),
            update_dry.stdout + update_dry.stderr,
        )
        updated = subprocess.run(
            ["bash", str(project / "scripts/update.sh"), "--platform", platform, "--no-commit"],
            cwd=target, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        invoked = command([sys.executable, str(helper_dest), "--help"], cwd=target, check=False) if helper_dest.exists() else updated
        emit(
            f"update-{platform}-restores-helper",
            updated.returncode == 0 and helper_dest.is_file() and invoked.returncode == 0,
            updated.stdout + updated.stderr,
        )
        emit(
            f"update-{platform}-restores-state-doc",
            updated.returncode == 0
            and state_doc_dest.is_file()
            and state_doc_dest.read_bytes() == (project / ".writ/docs/recommended-delivery-state-format.md").read_bytes(),
            updated.stdout + updated.stderr,
        )

        linked = workspace / f"unlink-{platform}"
        linked.mkdir()
        platform_dir = linked / f".{platform if platform != 'claude' else 'claude'}"
        platform_dir.mkdir()
        agent_source = project / ("codex/agents" if platform == "codex" else ("claude-code/agents" if platform == "claude" else "agents"))
        (platform_dir / "commands").symlink_to(project / "commands", target_is_directory=True)
        (platform_dir / "agents").symlink_to(agent_source, target_is_directory=True)
        (linked / "scripts").mkdir()
        (linked / "scripts/recommend-state.py").symlink_to(helper)
        (linked / ".writ/docs").mkdir(parents=True)
        linked_state_doc = linked / ".writ/docs/recommended-delivery-state-format.md"
        linked_state_doc.symlink_to(project / ".writ/docs/recommended-delivery-state-format.md")
        if platform == "cursor":
            (platform_dir / "rules").mkdir()
            (platform_dir / "rules/writ.mdc").symlink_to(project / "cursor/writ.mdc")
            (platform_dir / "system-instructions.md").symlink_to(project / "system-instructions.md")
        elif platform == "claude":
            (linked / "CLAUDE.md").symlink_to(project / "claude-code/CLAUDE.md")
        manifest = platform_dir / ".writ-manifest"
        write(manifest, f"# mode: link\n# platform: {platform}\n# version: fixture\n# link_target: {project}\n")
        unlink_dry = command(
            ["bash", str(project / "scripts/unlink.sh"), "--platform", platform, "--dry-run", "--no-commit"],
            cwd=linked, check=False,
        )
        emit(
            f"unlink-{platform}-dry-run-helper",
            unlink_dry.returncode == 0 and "scripts/recommend-state.py" in unlink_dry.stdout and (linked / "scripts/recommend-state.py").is_symlink(),
            unlink_dry.stdout + unlink_dry.stderr,
        )
        emit(
            f"unlink-{platform}-dry-run-state-doc",
            unlink_dry.returncode == 0
            and ".writ/docs/recommended-delivery-state-format.md" in unlink_dry.stdout
            and linked_state_doc.is_symlink(),
            unlink_dry.stdout + unlink_dry.stderr,
        )
        unlinked = command(
            ["bash", str(project / "scripts/unlink.sh"), "--platform", platform, "--no-commit"],
            cwd=linked, check=False,
        )
        unlinked_helper = linked / "scripts/recommend-state.py"
        invoked = command([sys.executable, str(unlinked_helper), "--help"], cwd=linked, check=False) if unlinked_helper.exists() else unlinked
        emit(
            f"unlink-{platform}-copies-helper",
            unlinked.returncode == 0 and unlinked_helper.is_file() and not unlinked_helper.is_symlink() and invoked.returncode == 0,
            unlinked.stdout + unlinked.stderr,
        )
        emit(
            f"unlink-{platform}-copies-state-doc",
            unlinked.returncode == 0 and linked_state_doc.is_file() and not linked_state_doc.is_symlink(),
            unlinked.stdout + unlinked.stderr,
        )
finally:
    shutil.rmtree(workspace, ignore_errors=True)
PY

  while IFS=$'\t' read -r scenario_status scenario_name scenario_reason; do
    [ -z "$scenario_status" ] && continue
    CURRENT_SCENARIOS=$((CURRENT_SCENARIOS + 1))
    if [ "$scenario_status" = "PASS" ]; then
      CURRENT_SCENARIOS_PASSED=$((CURRENT_SCENARIOS_PASSED + 1))
    else
      add_finding "scenario:$scenario_name" "$scenario_reason" "Fix the executable reducer or real disposable repository scenario."
    fi
  done < "$scenario_output"
  rm -f "$scenario_output"

  scenario_output="$(mktemp)"
  python3 "$PROJECT_ROOT/scripts/eval-recommend-state-adversarial.py" "$helper" > "$scenario_output"
  while IFS=$'\t' read -r scenario_status scenario_name scenario_reason; do
    [ -z "$scenario_status" ] && continue
    CURRENT_SCENARIOS=$((CURRENT_SCENARIOS + 1))
    if [ "$scenario_status" = "PASS" ]; then
      CURRENT_SCENARIOS_PASSED=$((CURRENT_SCENARIOS_PASSED + 1))
    else
      add_finding "adversarial:$scenario_name" "$scenario_reason" "Restore the evidence-derived Story 3 invariant exercised by this disposable-repository fixture."
    fi
  done < "$scenario_output"
  rm -f "$scenario_output"

  require_literal "$preamble" '### Narrow Recommended-Delivery Exception' "The preamble must define the narrow recommended-planning exception."
  require_literal "$preamble" 'planning commands create files and stop' "The preamble must preserve the default planning stop boundary."

  require_literal "$create_spec" 'Parse `--recommend` exactly once at command entry.' "Create-spec must parse recommendation mode once at entry."
  require_literal "$create_spec" 'Normal branch (authoritative): when `--recommend` is absent, follow every' "Create-spec must preserve normal behavior behind an explicit branch."
  require_literal "$create_spec" '### Authoritative `--recommend` Invocation Matrix' "Create-spec must define its fail-before-mutation invocation matrix."
  require_literal "$create_spec" '`/create-spec --recommend --from-issue <one-path>`' "Create-spec must support one issue source in recommendation mode."
  require_literal "$create_spec" '`/create-spec --recommend --from-prototype`' "Create-spec must support prototype source in recommendation mode."
  require_literal "$create_spec" '`/create-spec --recommend --quick`' "Create-spec must reject recommend plus quick."
  require_literal "$create_spec" '`/create-spec --recommend --force`' "Create-spec must reject recommend plus force."
  require_literal "$create_spec" 'multiple source modes' "Create-spec must reject multiple source modes."
  require_literal "$create_spec" 'Validate the complete invocation before' "Create-spec must validate invocation before file, issue, or state mutation."
  require_literal "$create_spec" 'recommendation-log.md' "Create-spec must create the tracked recommendation audit."
  require_literal "$create_spec" 'never triggers `/implement-spec`' "Create-spec recommended authoring must stop before implementation."

  require_literal "$helper" 'def validate_package(' "The executable helper must validate immutable packages."
  require_literal "$helper" 'def reconcile(' "The executable helper must reconcile canonical state."
  require_literal "$helper" 'def reserve_worktree(' "The executable helper must reserve keyed worktrees."
  require_literal "$helper" 'def normalize_result(' "The executable helper must normalize nested results."

  require_literal "$state_doc" '# Recommended Delivery State Format' "The canonical state-format document must exist."
  require_literal "$state_doc" '`recommend-execution-v1`' "The canonical document must define the runtime schema."
  require_literal "$state_doc" 'exclusive-create' "Execution state creation must be collision-safe."
  require_literal "$state_doc" 'sibling temporary file' "State replacement must be crash-safe."
  require_literal "$state_doc" 'preserve unknown fields' "Compatible writers must preserve unknown fields."
  require_literal "$state_doc" 'unsupported major' "Unsupported schema majors must block."
  require_literal "$state_doc" 'package_manifest' "The canonical document must define the package manifest."
  require_literal "$state_doc" 'owned-path/worktree snapshot' "The state contract must capture owned-path and worktree evidence."
  require_literal "$state_doc" '`delivery_context`' "The canonical document must define delivery context."
  require_literal "$state_doc" '`recommend-command-result-v1`' "The canonical document must define nested command results."
  require_literal "$state_doc" 'stable question ID' "Required-answer persistence must preserve stable interaction identity."
  require_literal "$state_doc" 'Saved markers are hints only' "Resume must treat persisted markers as hints."
  require_literal "$state_doc" 'repository-only reconciliation' "Story 3 reconciliation must exclude provider probes."
  require_literal "$state_doc" 'WWB incompleteness' "The canonical reconciliation contract must treat incomplete WWB as warning-only."
  require_literal "$state_doc" 'Story 3 still' "Story 3 must remain provider-free after Story 4 activation."
  require_literal "$state_doc" '`delivery.merge` and `delivery.release` remain inert for Story 5' "Story 5 fields must remain inert."
  require_literal "$state_doc" 'recommendation-log.md' "The canonical document must define the tracked recommendation log."
  require_literal "$state_doc" 'Compatibility and Versioning' "The canonical document must define schema evolution."

  require_literal "$recommendation_log" '# Recommendation Log: Recommended Autonomous Delivery' "The locked dogfood spec must include its tracked recommendation log."
  require_literal "$recommendation_log" '**Privacy:** Decisions and evidence only; no private chain-of-thought or transcript content' "The recommendation log must state its privacy boundary."
  require_literal "$recommendation_log" '**Selection:**' "The recommendation log must preserve selection source."
  require_literal "$recommendation_log" '**Result:**' "The recommendation log must preserve transition/artifact result."
}

check_recommended_staging() {
  local helper="$PROJECT_ROOT/scripts/recommend-state.py"
  local fake="$PROJECT_ROOT/scripts/eval-recommend-stage.py"
  local state_doc="$PROJECT_ROOT/.writ/docs/recommended-delivery-state-format.md"
  local implement_spec="$PROJECT_ROOT/commands/implement-spec.md"
  local config="$PROJECT_ROOT/.writ/docs/config-format.md"
  local adapter scenario_output scenario_status scenario_name scenario_reason

  scenario_output="$(mktemp)"
  if ! python3 "$fake" > "$scenario_output"; then
    :
  fi
  while IFS=$'\t' read -r scenario_status scenario_name scenario_reason; do
    case "$scenario_status" in
      PASS)
        CURRENT_SCENARIOS=$((CURRENT_SCENARIOS + 1))
        CURRENT_SCENARIOS_PASSED=$((CURRENT_SCENARIOS_PASSED + 1))
        ;;
      FAIL)
        CURRENT_SCENARIOS=$((CURRENT_SCENARIOS + 1))
        add_finding "story4:$scenario_name" "$scenario_reason" "Fix the local reducer or disposable provider fake."
        ;;
    esac
  done < "$scenario_output"
  rm -f "$scenario_output"

  for operation in activate_staging record_ship record_pr_lookup mark_pr_create_attempt record_pr_created finalize_pr_audit record_checks record_preview derive_uat record_uat record_approval revalidate_staging; do
    require_literal "$helper" "def ${operation}(" "The reducer must expose explicit ${operation} evidence handling."
  done
  require_literal "$state_doc" 'production_approved' "The canonical v1 state must stop Story 4 at durable production approval."
  require_literal "$state_doc" 'A lost response always re-enters lookup.' "PR mutation recovery must always re-lookup."
  require_literal "$state_doc" 'Repeated absence after authorization/attempt blocks' "PR mutation must be at-most-once."
  require_literal "$state_doc" 'Config checks are separately classified' "Configured checks must not replace provider discovery."
  require_literal "$state_doc" 'URL-pattern-only evidence is insufficient' "Preview URL patterns must not substitute for provenance."
  require_literal "$state_doc" '`record-uat` re-derives' "UAT evidence must be independently re-derived."
  require_literal "$state_doc" 'Cached fields alone never approve' "Approval must require fresh reconciliation."
  require_literal "$state_doc" 'marker-only success' "Ship evidence must be substantive and head-bound."
  require_literal "$state_doc" 'zero unresolved' "Later staging transitions must reject Pending mutation audits."
  require_literal "$state_doc" '`decisionId`' "Ship commit grouping must bind its finalized audit identity."
  require_literal "$state_doc" 'strict UTC RFC3339' "Approval evidence must enforce temporal freshness."
  require_literal "$state_doc" '`authenticated: true`' "Required-check discovery must prove authentication."
  require_literal "$state_doc" '`deployment-status → provider-deployment|provider-status`' "Preview source and provenance kind must agree."
  for key in "Delivery Provider" "Delivery Remote" "Preview Provider" "Preview Project" "Preview Evidence Source" "Preview URL Pattern" "Required Checks" "CI Wait Timeout" "Preview Wait Timeout"; do
    require_literal "$config" "\`$key\`" "Config documentation must define $key."
  done

  # ADR-013 (revised 2026-07-17): the single-spec staging->PR->production flow
  # is deferred but preserved dormant. Its contract stays falsifiable via the
  # reducer scenarios above, the state-format doc, and the config-format doc —
  # not via active command/adapter surfaces, which no longer carry it. The
  # human production boundary still forbids merge automation on every adapter.
  for adapter in "$PROJECT_ROOT/adapters/cursor.md" "$PROJECT_ROOT/adapters/claude-code.md" "$PROJECT_ROOT/adapters/codex.md"; do
    forbid_literal "$adapter" 'mergePullRequest' "Adapters must not expose merge operations (human production boundary)."
  done

  forbid_literal "$helper" 'deploy_to_vercel' "The local reducer must not deploy previews."
  forbid_literal "$helper" 'browser_navigate' "The local reducer must not automate browsers."
  forbid_literal "$helper" 'import requests' "The local reducer must not call provider HTTP APIs."
  forbid_literal "$helper" 'urllib.request' "The local reducer must not call provider HTTP APIs."
  forbid_literal "$implement_spec" 'npm publish' "Recommended staging must not publish packages."
}

check_spec_dependencies() {
  local fake="$PROJECT_ROOT/scripts/eval-spec-deps.py"
  local helper="$PROJECT_ROOT/scripts/spec-deps.py"
  local create_spec="$PROJECT_ROOT/commands/create-spec.md"
  local verify_spec="$PROJECT_ROOT/commands/verify-spec.md"
  local implement_phase="$PROJECT_ROOT/commands/implement-phase.md"
  local scenario_output scenario_status scenario_name scenario_reason

  scenario_output="$(mktemp)"
  if ! python3 "$fake" > "$scenario_output"; then
    :
  fi
  while IFS=$'\t' read -r scenario_status scenario_name scenario_reason; do
    case "$scenario_status" in
      PASS)
        CURRENT_SCENARIOS=$((CURRENT_SCENARIOS + 1))
        CURRENT_SCENARIOS_PASSED=$((CURRENT_SCENARIOS_PASSED + 1))
        ;;
      FAIL)
        CURRENT_SCENARIOS=$((CURRENT_SCENARIOS + 1))
        add_finding "spec-deps:$scenario_name" "$scenario_reason" "Fix the executable parser or the fixture scenario."
        ;;
    esac
  done < "$scenario_output"
  rm -f "$scenario_output"

  require_literal "$helper" 'def parse_header(' "The dependency helper must parse the spec-level header."
  require_literal "$helper" 'def validate_graph(' "The dependency helper must validate the cross-spec graph."
  require_literal "$helper" 'dependency_cycle' "The dependency helper must diagnose cross-spec cycles."

  require_literal "$create_spec" '> **Dependencies:**' "Create-spec must emit the authoritative Dependencies header."
  require_literal "$create_spec" 'exact spec-folder IDs' "Create-spec must document exact folder-ID dependency values."

  require_literal "$verify_spec" 'Cross-spec dependency validation' "Verify-spec Check 4 must validate cross-spec dependencies."
  require_literal "$verify_spec" 'self-reference' "Verify-spec must diagnose self-referential spec dependencies."
  require_literal "$verify_spec" 'story dependency validation is unchanged' "Verify-spec must keep story and spec dependency graphs distinct."

  require_literal "$implement_phase" 'Valid explicit `Dependencies` graph' "Implement-phase must treat the explicit graph as authoritative."
  require_literal "$implement_phase" 'topological' "Implement-phase must topologically order the explicit DAG."
  require_literal "$implement_phase" 'roadmap order' "Implement-phase must use roadmap order as the independent-spec tie-break."
  require_literal "$implement_phase" 'inference remains advisory' "Implement-phase must keep shared-surface inference advisory only."
  require_literal "$implement_phase" 'stop before the confirmation gate' "Implement-phase must stop before confirmation on an invalid graph."
}

check_phase_lanes() {
  local fake="$PROJECT_ROOT/scripts/eval-phase-lane.py"
  local helper="$PROJECT_ROOT/scripts/phase-state.py"
  local state_doc="$PROJECT_ROOT/.writ/docs/phase-execution-state-format.md"
  local implement_phase="$PROJECT_ROOT/commands/implement-phase.md"
  local implement_spec="$PROJECT_ROOT/commands/implement-spec.md"
  local cursor_adapter="$PROJECT_ROOT/adapters/cursor.md"
  local claude_adapter="$PROJECT_ROOT/adapters/claude-code.md"
  local codex_adapter="$PROJECT_ROOT/adapters/codex.md"
  local adapter scenario_output scenario_status scenario_name scenario_reason

  scenario_output="$(mktemp)"
  if ! python3 "$fake" > "$scenario_output"; then
    :
  fi
  while IFS=$'\t' read -r scenario_status scenario_name scenario_reason; do
    case "$scenario_status" in
      PASS)
        CURRENT_SCENARIOS=$((CURRENT_SCENARIOS + 1))
        CURRENT_SCENARIOS_PASSED=$((CURRENT_SCENARIOS_PASSED + 1))
        ;;
      FAIL)
        CURRENT_SCENARIOS=$((CURRENT_SCENARIOS + 1))
        add_finding "phase-lane:$scenario_name" "$scenario_reason" "Fix the phase-state reducer or the disposable-repo scenario."
        ;;
    esac
  done < "$scenario_output"
  rm -f "$scenario_output"

  require_literal "$helper" 'def cmd_create_lane(' "The reducer must create isolated lanes before work."
  require_literal "$helper" 'def validate_result(' "The reducer must validate the structured result."
  require_literal "$helper" 'def cmd_integrate(' "The reducer must merge only verified success."
  require_literal "$helper" 'def _atomic_write(' "The reducer must write phase state atomically."
  require_literal "$helper" 'preserved_lane' "The reducer must preserve non-successful lanes for Story 4."

  require_literal "$state_doc" 'phase-execution-v2' "The state-format doc must define the canonical schema."
  require_literal "$state_doc" 'phase-spec-result-v1' "The state-format doc must define the structured result."
  require_literal "$state_doc" 'Isolation Begins Before Work' "The state-format doc must require pre-work isolation."
  require_literal "$state_doc" 'never forwards' "The state-format doc must forbid forwarding conversational transcript."
  require_literal "$state_doc" 'os.replace' "The state-format doc must define crash-safe atomic writes."

  require_literal "$implement_phase" 'fresh subagent' "Implement-phase must launch a fresh subagent per spec."
  require_literal "$implement_phase" 'writ/phase/{phase-id}/{spec-id}' "Implement-phase must own the lane branch naming."
  require_literal "$implement_phase" 'phase-spec-result-v1' "Implement-phase must validate the structured result."
  require_literal "$implement_phase" 'only a verified' "Implement-phase must merge only verified success."
  require_literal "$implement_phase" 'scripts/phase-state.py' "Implement-phase must reference the executable reducer."

  require_literal "$implement_spec" 'supplied lane' "Implement-spec must execute only inside the supplied lane."
  require_literal "$implement_spec" 'phase-spec-result-v1' "Implement-spec must return the structured result."
  require_literal "$implement_spec" 'must not mutate the parent checkout' "Implement-spec must not touch the parent checkout in lane mode."

  for adapter in "$cursor_adapter" "$claude_adapter" "$codex_adapter"; do
    require_literal "$adapter" '### Fresh Isolated Execution Lanes' "Each adapter must map fresh isolated execution."
    require_literal "$adapter" 'phase-spec-result-v1' "Each adapter must return the structured result."
    require_literal "$adapter" 'no prior conversational transcript' "Each adapter must seed fresh context without transcript."
    require_literal "$adapter" 'isolated worktree' "Each adapter must map the isolated worktree."
  done
}

check_phase_challenges() {
  local fake="$PROJECT_ROOT/scripts/eval-phase-challenge.py"
  local helper="$PROJECT_ROOT/scripts/phase-state.py"
  local preamble="$PROJECT_ROOT/commands/_preamble.md"
  local state_doc="$PROJECT_ROOT/.writ/docs/phase-execution-state-format.md"
  local implement_phase="$PROJECT_ROOT/commands/implement-phase.md"
  local implement_spec="$PROJECT_ROOT/commands/implement-spec.md"
  local scenario_output scenario_status scenario_name scenario_reason

  scenario_output="$(mktemp)"
  if ! python3 "$fake" > "$scenario_output"; then
    :
  fi
  while IFS=$'\t' read -r scenario_status scenario_name scenario_reason; do
    case "$scenario_status" in
      PASS)
        CURRENT_SCENARIOS=$((CURRENT_SCENARIOS + 1))
        CURRENT_SCENARIOS_PASSED=$((CURRENT_SCENARIOS_PASSED + 1))
        ;;
      FAIL)
        CURRENT_SCENARIOS=$((CURRENT_SCENARIOS + 1))
        add_finding "phase-challenge:$scenario_name" "$scenario_reason" "Fix the challenge validator or the scenario."
        ;;
    esac
  done < "$scenario_output"
  rm -f "$scenario_output"

  require_literal "$helper" 'def validate_challenge(' "The reducer must validate the four-part challenge."
  require_literal "$helper" 'CHALLENGE_TRIGGERS' "The reducer must constrain challenge triggers."
  require_literal "$helper" 'invalid_challenge' "A malformed challenge must be a contract error."

  require_literal "$preamble" '## User Challenge' "The preamble must define the User Challenge contract."
  require_literal "$preamble" 'scope_degradation' "The preamble must constrain the challenge trigger."
  require_literal "$preamble" 'select-or-pause' "The preamble must apply the evidence-based select-or-pause rule."
  require_literal "$preamble" 'four required parts' "The preamble must require all four challenge parts."

  require_literal "$state_doc" '## User Challenges' "The state-format doc must define persisted challenges."
  require_literal "$state_doc" 'unresolved' "The state-format doc must persist unresolved challenges."

  require_literal "$implement_spec" 'challenge_required' "Implement-spec must return challenge_required when it cannot self-decide."
  require_literal "$implement_spec" 'select-or-pause' "Implement-spec must apply the select-or-pause boundary."

  require_literal "$implement_phase" 'User Challenge' "Implement-phase must present User Challenges."
  require_literal "$implement_phase" 'ordinary failures use their normal' "Implement-phase must not wrap ordinary failures as challenges."
}

check_phase_quarantine() {
  local fake="$PROJECT_ROOT/scripts/eval-phase-quarantine.py"
  local helper="$PROJECT_ROOT/scripts/phase-state.py"
  local state_doc="$PROJECT_ROOT/.writ/docs/phase-execution-state-format.md"
  local implement_phase="$PROJECT_ROOT/commands/implement-phase.md"
  local implement_spec="$PROJECT_ROOT/commands/implement-spec.md"
  local status_cmd="$PROJECT_ROOT/commands/status.md"
  local cursor_adapter="$PROJECT_ROOT/adapters/cursor.md"
  local claude_adapter="$PROJECT_ROOT/adapters/claude-code.md"
  local codex_adapter="$PROJECT_ROOT/adapters/codex.md"
  local adapter scenario_output scenario_status scenario_name scenario_reason

  scenario_output="$(mktemp)"
  if ! python3 "$fake" > "$scenario_output"; then
    :
  fi
  while IFS=$'\t' read -r scenario_status scenario_name scenario_reason; do
    case "$scenario_status" in
      PASS)
        CURRENT_SCENARIOS=$((CURRENT_SCENARIOS + 1))
        CURRENT_SCENARIOS_PASSED=$((CURRENT_SCENARIOS_PASSED + 1))
        ;;
      FAIL)
        CURRENT_SCENARIOS=$((CURRENT_SCENARIOS + 1))
        add_finding "phase-quarantine:$scenario_name" "$scenario_reason" "Fix the quarantine/reconcile reducer or the disposable-repo scenario."
        ;;
    esac
  done < "$scenario_output"
  rm -f "$scenario_output"

  require_literal "$helper" 'def cmd_quarantine(' "The reducer must implement terminal quarantine."
  require_literal "$helper" 'def cmd_reconcile(' "The reducer must implement read-only resume reconciliation."
  require_literal "$helper" 'writ/quarantine/' "The reducer must name the quarantine branch."
  require_literal "$helper" 'skipped_blocked' "The reducer must block declared dependents."
  require_literal "$helper" 'retry_exhausted' "The reducer must bound retries."

  require_literal "$state_doc" '## Quarantine and Resume' "The state-format doc must define quarantine and resume."
  require_literal "$state_doc" 'skipped_blocked' "The state-format doc must record blocked dependents."
  require_literal "$state_doc" 'reconcile' "The state-format doc must define resume reconciliation."

  require_literal "$implement_phase" 'writ/quarantine/{spec-id}' "Implement-phase must quarantine terminal failures."
  require_literal "$implement_phase" 'one transient retry' "Implement-phase must permit exactly one transient retry."
  require_literal "$implement_phase" 'skipped_blocked' "Implement-phase must block dependents and continue independents."
  require_literal "$implement_phase" 'does not guess or mutate git' "Resume must never guess or mutate git on mismatch."

  require_literal "$implement_spec" 'transient' "Implement-spec must classify transient failures."
  require_literal "$implement_spec" 'terminal' "Implement-spec must classify terminal failures."

  require_literal "$status_cmd" 'quarantine' "Status must surface quarantine branches read-only."

  for adapter in "$cursor_adapter" "$claude_adapter" "$codex_adapter"; do
    require_literal "$adapter" '### Quarantine and Resume' "Each adapter must map quarantine and resume mechanics."
    require_literal "$adapter" 'writ/quarantine/' "Each adapter must name the quarantine branch."
  done
}

check_phase_knowledge() {
  local fake="$PROJECT_ROOT/scripts/eval-phase-knowledge.py"
  local helper="$PROJECT_ROOT/scripts/phase-state.py"
  local state_doc="$PROJECT_ROOT/.writ/docs/phase-execution-state-format.md"
  local implement_phase="$PROJECT_ROOT/commands/implement-phase.md"
  local knowledge_cmd="$PROJECT_ROOT/commands/knowledge.md"
  local scenario_output scenario_status scenario_name scenario_reason

  scenario_output="$(mktemp)"
  if ! python3 "$fake" > "$scenario_output"; then
    :
  fi
  while IFS=$'\t' read -r scenario_status scenario_name scenario_reason; do
    case "$scenario_status" in
      PASS)
        CURRENT_SCENARIOS=$((CURRENT_SCENARIOS + 1))
        CURRENT_SCENARIOS_PASSED=$((CURRENT_SCENARIOS_PASSED + 1))
        ;;
      FAIL)
        CURRENT_SCENARIOS=$((CURRENT_SCENARIOS + 1))
        add_finding "phase-knowledge:$scenario_name" "$scenario_reason" "Fix the writeback evaluator or the fixture."
        ;;
    esac
  done < "$scenario_output"
  rm -f "$scenario_output"

  require_literal "$helper" 'def knowledge_writeback(' "The reducer must implement phase-close writeback."
  require_literal "$helper" 'def _is_duplicate(' "The reducer must substantively deduplicate candidates."
  require_literal "$helper" 'adr-scale' "The reducer must reject ADR-scale candidates."

  require_literal "$state_doc" '## Knowledge Writeback' "The state-format doc must define phase-close knowledge."
  require_literal "$state_doc" 'knowledgeWritten' "The state-format doc must make writeback resume-safe."
  require_literal "$state_doc" 'no-op' "The state-format doc must define the no-candidate no-op."

  require_literal "$implement_phase" 'evidence-bound' "Implement-phase must apply evidence-bound knowledge gates."
  require_literal "$implement_phase" 'no qualifying candidate' "Implement-phase must treat no qualifying candidate as a no-op."

  require_literal "$knowledge_cmd" 'Phase-Close Writeback' "Knowledge must document phase-close writeback."
  require_literal "$knowledge_cmd" 'substantive' "Knowledge must deduplicate candidates substantively."
}

check_phase_health() {
  local fake="$PROJECT_ROOT/scripts/eval-phase-health.py"
  local helper="$PROJECT_ROOT/scripts/phase-state.py"
  local state_doc="$PROJECT_ROOT/.writ/docs/phase-execution-state-format.md"
  local implement_phase="$PROJECT_ROOT/commands/implement-phase.md"
  local status_cmd="$PROJECT_ROOT/commands/status.md"
  local scenario_output scenario_status scenario_name scenario_reason

  scenario_output="$(mktemp)"
  if ! python3 "$fake" > "$scenario_output"; then
    :
  fi
  while IFS=$'\t' read -r scenario_status scenario_name scenario_reason; do
    case "$scenario_status" in
      PASS)
        CURRENT_SCENARIOS=$((CURRENT_SCENARIOS + 1))
        CURRENT_SCENARIOS_PASSED=$((CURRENT_SCENARIOS_PASSED + 1))
        ;;
      FAIL)
        CURRENT_SCENARIOS=$((CURRENT_SCENARIOS + 1))
        add_finding "phase-health:$scenario_name" "$scenario_reason" "Fix the progress/health reducer or the fixture."
        ;;
    esac
  done < "$scenario_output"
  rm -f "$scenario_output"

  require_literal "$helper" 'def cmd_progress(' "The reducer must expose read-only phase progress."
  require_literal "$helper" 'def cmd_health(' "The reducer must compute categorical health."
  require_literal "$helper" 'Attention' "Health must be able to require attention."

  require_literal "$state_doc" '## Progress and Health' "The state-format doc must define progress and health."
  require_literal "$state_doc" 'categorical' "Health must be categorical, not a score."

  require_literal "$implement_phase" 'production health' "Implement-phase must report phase progress and production health."

  require_literal "$status_cmd" 'phase progress' "Status must surface phase progress."
  require_literal "$status_cmd" 'read-only' "Status must remain read-only."
}

check_ralph_retirement() {
  local changelog="$PROJECT_ROOT/CHANGELOG.md"
  local skill="$PROJECT_ROOT/SKILL.md"
  local archived active surface

  # Preserved (archived, not deleted) with recognizable grouping.
  for archived in ralph.md ralph.sh PROMPT_build.md ralph-cli-pipeline.md ralph-state-format.md README.md; do
    if [ ! -f "$PROJECT_ROOT/archive/ralph/$archived" ]; then
      add_finding "archive/ralph/$archived" "Ralph must be archived, not deleted." "git mv the Ralph artifact into archive/ralph/ (with a landing README.md)."
    fi
  done

  # Removed from every active location.
  for active in commands/ralph.md scripts/ralph.sh scripts/PROMPT_build.md \
                .writ/docs/ralph-cli-pipeline.md .writ/docs/ralph-state-format.md; do
    if [ -f "$PROJECT_ROOT/$active" ]; then
      add_finding "$active" "Ralph artifact must not remain on an active surface." "Move it into archive/ralph/."
    fi
  done

  # No Ralph reference on active command, catalog, config, adapter, README, or
  # status surfaces. Historical specs, ADRs, roadmap/mission history, the
  # changelog, and archive/ are deliberately excluded from this allowlisted search.
  for surface in "$PROJECT_ROOT/.writ/manifest.yaml" \
                 "$skill" \
                 "$PROJECT_ROOT/.writ/docs/config-format.md" \
                 "$PROJECT_ROOT/README.md" \
                 "$PROJECT_ROOT/commands/status.md" \
                 "$PROJECT_ROOT/commands/implement-phase.md" \
                 "$PROJECT_ROOT/scripts/gen-skill.sh" \
                 "$PROJECT_ROOT/codex/AGENTS.md.template" \
                 "$PROJECT_ROOT/claude-code/CLAUDE.md" \
                 "$PROJECT_ROOT/system-instructions.md" \
                 "$PROJECT_ROOT/cursor/writ.mdc" \
                 "$PROJECT_ROOT/adapters/cursor.md" \
                 "$PROJECT_ROOT/adapters/claude-code.md" \
                 "$PROJECT_ROOT/adapters/codex.md" \
                 "$PROJECT_ROOT/adapters/openclaw.md"; do
    forbid_literal_ci "$surface" "ralph" "Active surface must not reference the retired Ralph loop; redirect users to /implement-phase."
  done

  # Catalog presents the supported supervised replacement.
  require_literal "$skill" 'implement-phase' "The generated catalog must present /implement-phase as the supervised path."

  # Changelog records the retirement, the archive location, the supported
  # replacement, and the finish-or-abandon-before-upgrade warning.
  require_literal "$changelog" 'archive/ralph/' "The changelog must record where Ralph was archived."
  require_literal "$changelog" '/implement-phase' "The changelog must direct multi-spec work to /implement-phase."
  require_literal "$changelog" 'Finish or abandon any in-flight' "The changelog must warn users to finish or abandon in-flight Ralph runs before upgrading."
}

check_memory_interop() {
  local adapter
  local canonical='the reviewable markdown layer that feeds'
  local skill="$PROJECT_ROOT/skills/gbrain-interop/SKILL.md"
  local manifest="$PROJECT_ROOT/.writ/manifest.yaml"
  local catalog="$PROJECT_ROOT/SKILL.md"
  local recipe="$PROJECT_ROOT/.writ/docs/gbrain-recipe.md"
  local mission="$PROJECT_ROOT/.writ/product/mission.md"
  local readme="$PROJECT_ROOT/README.md"

  # (1) Every adapter carries the native-memory section and the identical
  #     two-place rule (asserted by a stable key phrase from the canonical
  #     sentence), so a drifting edit fails CI instead of silently diverging.
  for adapter in cursor claude-code codex openclaw; do
    require_literal "$PROJECT_ROOT/adapters/$adapter.md" 'Native Memory & the Writ Ledger' \
      "adapters/$adapter.md must carry the 'Native Memory & the Writ Ledger' section."
    require_literal "$PROJECT_ROOT/adapters/$adapter.md" "$canonical" \
      "adapters/$adapter.md must state the canonical two-place rule ('$canonical')."
    require_literal "$PROJECT_ROOT/adapters/$adapter.md" 'gbrain-interop' \
      "adapters/$adapter.md must cross-link the gbrain-interop skill for the external-index layer."
  done

  # (2) The sibling gbrain-compatibility-recipe artifacts exist and are
  #     registered. If any of these fail the run order is wrong — fix the
  #     order, never weaken the assertion.
  require_literal "$skill" 'name: gbrain-interop' "The gbrain-interop skill must exist at skills/gbrain-interop/SKILL.md."
  require_literal "$manifest" 'gbrain-interop' "gbrain-interop must be registered in .writ/manifest.yaml."
  require_literal "$catalog" 'gbrain-interop' "gbrain-interop must appear in the root SKILL.md catalog."

  # (3) The recipe exists and states the round-trip / graceful-absence guarantee.
  require_literal "$recipe" 'round-trip' ".writ/docs/gbrain-recipe.md must state the round-trip guarantee."
  require_literal "$recipe" 'byte-for-byte' ".writ/docs/gbrain-recipe.md must guarantee the ledger stays byte-for-byte intact when the index is removed."

  # (4) No stale mission framing survives on active surfaces (historical ADRs,
  #     specs, and the roadmap that describe the change are left untouched).
  for surface in "$mission" "$readme"; do
    forbid_literal "$surface" "persistent-database knowledge layer" \
      "Active surface must not carry the stale 'persistent-database knowledge layer' framing; the mission now reads 'not a memory database or retrieval engine'."
  done
}

check_skill_lifecycle() {
  local fake="$PROJECT_ROOT/scripts/eval-skill-lifecycle.py"
  local lint="$PROJECT_ROOT/scripts/lint-skill.sh"
  local skills_doc="$PROJECT_ROOT/.writ/docs/skills.md"
  local scenario_output scenario_status scenario_name scenario_reason

  # SHARED-ADDITIVE with 2026-07-10-skill-extraction: this is the single
  # skill-lifecycle function and CHECKS entry this spec appends. The extraction
  # spec appends its own distinct check in its own region.
  scenario_output="$(mktemp)"
  if ! python3 "$fake" > "$scenario_output"; then
    :
  fi
  while IFS=$'\t' read -r scenario_status scenario_name scenario_reason; do
    case "$scenario_status" in
      PASS)
        CURRENT_SCENARIOS=$((CURRENT_SCENARIOS + 1))
        CURRENT_SCENARIOS_PASSED=$((CURRENT_SCENARIOS_PASSED + 1))
        ;;
      FAIL)
        CURRENT_SCENARIOS=$((CURRENT_SCENARIOS + 1))
        add_finding "skill-lifecycle:$scenario_name" "$scenario_reason" "Fix the lifecycle lint in scripts/lint-skill.sh or the fixture expectation."
        ;;
    esac
  done < "$scenario_output"
  rm -f "$scenario_output"

  require_literal "$lint" 'candidate|proven|promoted' "The lint must enforce the closed lifecycle vocabulary."
  require_literal "$lint" 'State is EARNED from evidence' "The lint must document the earned-state contract."
  require_literal "$lint" 'Lifecycle-unearned' "The lint must emit an unearned-state finding category."
  require_literal "$lint" 'Lifecycle-evidence' "The lint must emit a malformed-evidence finding category."

  require_literal "$skills_doc" 'Skill Lifecycle' "The skills doc must document the lifecycle."
  require_literal "$skills_doc" 'earned from evidence' "The skills doc must explain earned-state semantics."
  require_literal "$skills_doc" 'type: promotion' "The skills doc must document the promotion evidence type."
}

check_refresh_evidence() {
  local fake="$PROJECT_ROOT/scripts/eval-refresh-evidence.py"
  local command_file="$PROJECT_ROOT/commands/refresh-command.md"
  local log_format="$PROJECT_ROOT/.writ/docs/refresh-log-format.md"
  local scenario_output scenario_status scenario_name scenario_reason

  scenario_output="$(mktemp)"
  if ! python3 "$fake" > "$scenario_output"; then
    :
  fi
  while IFS=$'\t' read -r scenario_status scenario_name scenario_reason; do
    case "$scenario_status" in
      PASS)
        CURRENT_SCENARIOS=$((CURRENT_SCENARIOS + 1))
        CURRENT_SCENARIOS_PASSED=$((CURRENT_SCENARIOS_PASSED + 1))
        ;;
      FAIL)
        CURRENT_SCENARIOS=$((CURRENT_SCENARIOS + 1))
        add_finding "refresh-evidence:$scenario_name" "$scenario_reason" "Fix the evidence validator in scripts/eval-refresh-evidence.py or the fixture expectation."
        ;;
    esac
  done < "$scenario_output"
  rm -f "$scenario_output"

  # The validator must define the parser and the grandfathering boundary.
  require_literal "$fake" 'def validate_entry(' "The fixture script must define the refresh-evidence validator."
  require_literal "$fake" 'LEARNING_CONTRACT_SINCE' "The validator must grandfather pre-contract entries by date."

  # Tier 2 (Story 3): the structural gate and allowlist, never an LLM judge.
  require_literal "$fake" 'def gate_decision(' "The fixture script must model the pre-merge gate decision."
  require_literal "$fake" 'def structural_tier2(' "The fixture script must model the structural Tier 2 check."
  require_literal "$fake" 'HIGH_TRAFFIC' "The fixture script must scope Tier 2 to the high-traffic allowlist."

  # The command must mandate the structured Evidence block and the rejection path.
  require_literal "$command_file" '**Evidence:**' "refresh-command Phase 3 must mandate a structured Evidence block per amendment."
  require_literal "$command_file" '**Rejected:**' "refresh-command Phase 4 must record rejected candidates."
  require_literal "$command_file" 'no evidence' "refresh-command must reject unevidenced proposals with reason 'no evidence'."
  require_literal "$command_file" 'eval failed' "refresh-command must reject eval-failing proposals with reason 'eval failed'."
  require_literal "$command_file" 'verbatim private transcript bodies' "refresh-command must forbid storing verbatim private transcript bodies (Prime Directive privacy)."

  # Story 3: the command must wire the pre-merge gate, the Tier 2 allowlist, the
  # structural-not-LLM boundary, and document the two-example acceptance.
  require_literal "$command_file" 'bash scripts/eval.sh --check=refresh-evidence' "refresh-command Phase 4 must run the pre-merge eval gate."
  require_literal "$command_file" 'high-traffic allowlist — `create-spec`, `implement-story`, `ship`, `refactor`' "refresh-command must scope Tier 2 to the high-traffic allowlist."
  require_literal "$command_file" 'structural only — not an LLM-as-judge' "refresh-command must keep Tier 2 structural and defer the LLM-judge variant."
  require_literal "$command_file" 'rejected for lacking evidence' "refresh-command must document the two-example acceptance (merged + rejected)."

  # The log-format doc must describe the same enforced contract.
  require_literal "$log_format" '**Evidence:**' "The refresh-log format must document the mandatory Evidence block."
  require_literal "$log_format" 'LEARNING_CONTRACT_SINCE' "The refresh-log format must document grandfathering."
  require_literal "$log_format" 'no evidence' "The refresh-log format must document the 'no evidence' rejection reason."
  require_literal "$log_format" 'eval failed' "The refresh-log format must document the 'eval failed' rejection reason."
}

check_knowledge_consolidate() {
  local fake="$PROJECT_ROOT/scripts/eval-knowledge-consolidate.py"
  local reducer="$PROJECT_ROOT/scripts/knowledge-consolidate.py"
  local knowledge_cmd="$PROJECT_ROOT/commands/knowledge.md"
  local retro_cmd="$PROJECT_ROOT/commands/retro.md"
  local readme="$PROJECT_ROOT/.writ/knowledge/README.md"
  local scenario_output scenario_status scenario_name scenario_reason

  # SHARED-ADDITIVE with 2026-07-10-evidence-bound-refresh: this spec appends
  # exactly one check function plus one CHECKS entry. Neither reorders nor
  # rewrites existing registry entries; sequential phase execution keeps the
  # two appends collision-free.
  scenario_output="$(mktemp)"
  if ! python3 "$fake" > "$scenario_output"; then
    :
  fi
  while IFS=$'\t' read -r scenario_status scenario_name scenario_reason; do
    case "$scenario_status" in
      PASS)
        CURRENT_SCENARIOS=$((CURRENT_SCENARIOS + 1))
        CURRENT_SCENARIOS_PASSED=$((CURRENT_SCENARIOS_PASSED + 1))
        ;;
      FAIL)
        CURRENT_SCENARIOS=$((CURRENT_SCENARIOS + 1))
        add_finding "knowledge-consolidate:$scenario_name" "$scenario_reason" "Fix the consolidation reducer in scripts/knowledge-consolidate.py or the fixture expectation."
        ;;
    esac
  done < "$scenario_output"
  rm -f "$scenario_output"

  # The reducer must reuse the substrate similarity metric and preserve lineage.
  require_literal "$reducer" 'def _tokens(' "The reducer must reuse the phase-state token set for duplicate detection."
  require_literal "$reducer" 'def detect_duplicates(' "The reducer must detect duplicate merge candidates."
  require_literal "$reducer" 'def detect_contradictions(' "The reducer must surface contradictions for human review."
  require_literal "$reducer" 'def detect_stale(' "The reducer must flag stale entries on observable signals."
  require_literal "$reducer" 'superseded_by' "The reducer must write superseded_by tombstone lineage."
  require_literal "$reducer" 'replaces' "The reducer must write replaces lineage on the canonical entry."
  require_literal "$reducer" 'unified_diff' "The reducer must emit a reviewable preview diff via difflib."
  require_literal "$reducer" 'merge, never append' "The reducer must state the merge-never-append principle."

  # The command must expose the gated, non-destructive consolidate mode.
  require_literal "$knowledge_cmd" '--consolidate' "Knowledge must route the --consolidate mode."
  require_literal "$knowledge_cmd" 'merge, never append' "Knowledge --consolidate must state the merge-never-append principle."
  require_literal "$knowledge_cmd" 'AskQuestion' "Knowledge --consolidate must gate every write on explicit approval."
  require_literal "$knowledge_cmd" 'does not commit' "Knowledge --consolidate must leave a reviewable diff without committing."

  # The retro hook must be a read-only advisory nudge only.
  require_literal "$retro_cmd" '/knowledge --consolidate' "Retro must nudge toward consolidation on a growth signal."
  require_literal "$retro_cmd" 'read-only' "The retro consolidation hook must remain read-only."
  require_literal "$retro_cmd" 'mutates no knowledge file' "The retro hook must never mutate the ledger."

  # The README must document lineage and the consolidation workflow.
  require_literal "$readme" 'Consolidation and Lineage' "The knowledge README must document the consolidation workflow."
  require_literal "$readme" 'superseded_by' "The knowledge README must document the superseded_by lineage field."
  require_literal "$readme" 'replaces' "The knowledge README must document the replaces lineage field."
  require_literal "$readme" 'merge, never append' "The knowledge README must state the merge-never-append principle."
}

check_leanness() {
  # Tier A leanness tripwire (dogfooding-only self-governance). Structural
  # findings (registry parity, missing baseline) FAIL the run via add_finding;
  # count/weight growth is surfaced via add_note as non-blocking warnings so the
  # check stays exit 0. Manifest parity (check_manifest), per-file length
  # (check_length), and skill boundary (skill-lifecycle) are intentionally NOT
  # duplicated here.
  local helper="$PROJECT_ROOT/scripts/eval-leanness.py"
  local baseline="$PROJECT_ROOT/.writ/leanness-baseline.json"
  local json tsv kind a b c

  if [ ! -f "$helper" ]; then
    RUN_ERRORS=$((RUN_ERRORS + 1))
    add_finding "scripts/eval-leanness.py" "leanness helper is missing." "Restore scripts/eval-leanness.py (leanness-guardian spec, Story 1)."
    return
  fi

  json="$(mktemp)"
  if ! python3 "$helper" --root "$PROJECT_ROOT" --baseline "$baseline" > "$json"; then
    RUN_ERRORS=$((RUN_ERRORS + 1))
    add_finding "scripts/eval-leanness.py" "leanness helper failed to run." "Run python3 scripts/eval-leanness.py for the traceback."
    rm -f "$json"
    return
  fi

  tsv="$(mktemp)"
  python3 - "$json" > "$tsv" <<'PY'
import json, sys
data = json.load(open(sys.argv[1]))
def clean(value): return str(value).replace("\t", " ").replace("\n", " ")
for item in data.get("structural", []):
    print("STRUCT\t%s\t%s\t%s" % (clean(item.get("subject", "")), clean(item.get("what", "")), clean(item.get("fix", ""))))
for item in data.get("warnings", []):
    print("WARN\t%s\t%s\t%s" % (clean(item.get("subject", "")), clean(item.get("what", "")), clean(item.get("fix", ""))))
m = data.get("metrics", {})
print("METRIC\tcommands=%s agents=%s skills=%s command_lines=%s command_chars=%s" % (
    m.get("commands"), m.get("agents"), m.get("skills"), m.get("command_lines"), m.get("command_chars")))
PY

  while IFS=$'\t' read -r kind a b c; do
    case "$kind" in
      STRUCT)
        add_finding "$a" "$b" "$c"
        ;;
      WARN)
        add_note "WARNING [$a]: $b Remediation: $c"
        ;;
      METRIC)
        add_note "Metrics: $a"
        ;;
    esac
  done < "$tsv"

  rm -f "$json" "$tsv"
}

run_check() {
  local check="$1"
  local func="check_${check//-/_}"

  CURRENT_CHECK="$check"
  CURRENT_FINDINGS=0
  CURRENT_NOTES=0
  CURRENT_SCENARIOS=0
  CURRENT_SCENARIOS_PASSED=0
  CURRENT_STATIC_ASSERTIONS=0
  CURRENT_STATIC_ASSERTIONS_PASSED=0
  CHECK_TMP="$(mktemp)"
  NOTE_TMP="$(mktemp)"

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
    if [ "$CURRENT_SCENARIOS" -gt 0 ]; then
      echo ""
      echo "Scenarios: $CURRENT_SCENARIOS_PASSED/$CURRENT_SCENARIOS passed"
    fi
    if [ "$CURRENT_STATIC_ASSERTIONS" -gt 0 ]; then
      echo "Supplementary static assertions: $CURRENT_STATIC_ASSERTIONS_PASSED/$CURRENT_STATIC_ASSERTIONS passed"
    fi
    if [ "$CURRENT_NOTES" -gt 0 ]; then
      echo ""
      echo "Notes (non-blocking):"
      cat "$NOTE_TMP"
    fi
  } >> "$REPORT_PATH"

  rm -f "$CHECK_TMP" "$NOTE_TMP"
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

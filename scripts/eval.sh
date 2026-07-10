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
)

TOTAL_FINDINGS=0
RUN_ERRORS=0
CURRENT_CHECK=""
CURRENT_FINDINGS=0
CHECK_TMP=""
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
  require_literal "$adr" 'Multi-spec `/implement-phase --recommend` remains excluded.' "ADR-013 must preserve the multi-spec recommended-execution exclusion."
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
  require_literal "$roadmap" 'Multi-spec `/implement-phase --recommend` remains excluded.' "The roadmap must preserve the multi-spec recommended-execution exclusion."

  require_literal "$mission" 'commands that explicitly support `--recommend`' "The product mission must describe the narrow command-supported exception."
  require_literal "$mission_lite" 'single-spec `--recommend` delivery' "The lite mission must preserve the bounded single-spec policy."
  require_literal "$ralph_adr" "[ADR-013]" "ADR-012 must distinguish Ralph retirement from bounded recommended delivery."

  require_literal "$system" 'only when the invoked command explicitly documents support for `--recommend`' "The system policy must limit the exception to commands that explicitly support --recommend."
  require_literal "$system" "observable evidence and durable audit summaries" "The system policy must require observable evidence and durable audit summaries."
  require_literal "$system" "exact reviewed PR head SHA" "The system policy must preserve one SHA-bound production approval."
  require_literal "$system" "branch protection, required checks, authentication, or authorization" "The system policy must preserve platform protection and authentication boundaries."
  require_literal "$system" "exclude private chain-of-thought" "The system policy must keep audit summaries free of private reasoning."
  require_literal "$cursor_rule" 'only when the invoked command explicitly documents support for `--recommend`' "The Cursor rule mirror must preserve the narrow recommended-delivery exception."

  forbid_literal "$phase_spec" "human *in the loop* at contract level" "Phase 6 still contains the superseded contract-level human gate."
  forbid_literal "$phase_spec" "never auto-decided" "Phase 6 still contains unconditional User Challenge decision language."
  forbid_literal "$phase_lite" "Any unattended mode" "The Phase 6 lite contract still forbids all unattended modes rather than opaque unbounded loops."
  forbid_literal "$phase_story_3" "selectable options rather than a local decision" "Phase 6 Story 3 still prohibits evidence-based local selection categorically."
  forbid_literal "$roadmap" "in the loop at contract level" "The roadmap still contains the superseded contract-level human gate."
  forbid_literal "$roadmap" "Never auto-decided." "The roadmap still contains unconditional User Challenge decision language."
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
  local implement_spec="$PROJECT_ROOT/commands/implement-spec.md"
  local implement_story="$PROJECT_ROOT/commands/implement-story.md"
  local state_doc="$PROJECT_ROOT/.writ/docs/recommended-delivery-state-format.md"
  local helper="$PROJECT_ROOT/scripts/recommend-state.py"
  local recommendation_log="$PROJECT_ROOT/.writ/specs/2026-07-10-recommended-autonomous-delivery/recommendation-log.md"
  local cursor_adapter="$PROJECT_ROOT/adapters/cursor.md"
  local claude_adapter="$PROJECT_ROOT/adapters/claude-code.md"
  local codex_adapter="$PROJECT_ROOT/adapters/codex.md"
  local adapter
  local scenario_output

  scenario_output="$(mktemp)"
  python3 - "$create_spec" "$implement_spec" "$state_doc" > "$scenario_output" <<'PY'
import json
import re
import sys

create_path, implement_path, state_path = sys.argv[1:]
create = open(create_path, encoding="utf-8").read()
implement = open(implement_path, encoding="utf-8").read()
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
implement_rows = table_after(implement, "### Authoritative `--recommend` Invocation Matrix")

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
    "`--recommend --resume`",
    "`--recommend` with `--dry-run`, `--draft`, `--no-split`, `--skip-gate`, or `--no-tag`",
):
    outcome = create_rows.get(invocation, "")
    mutation_sentinel = not outcome.startswith("Reject")
    emit("create-reject-before-mutation-" + str(len(invocation)) + "-" + invocation.split()[0].strip("`/"), outcome.startswith("Reject") and not mutation_sentinel, f"{invocation} must reject before the mutation sentinel")

for invocation in (
    "`/implement-spec --recommend <one-spec>`",
    "Internal recommended call with one valid `delivery_context`",
    "`/implement-spec --recommend --resume <execution-id>`",
):
    emit("implement-valid-" + invocation[:24].replace(" ", "_"), implement_rows.get(invocation, "").startswith("Supported"), f"{invocation} is not a supported structured matrix row")

for invocation in (
    "`/implement-spec --recommend --quick`",
    "`/implement-spec --recommend --force`",
    "`/implement-spec --recommend --from <story>`",
    "`/implement-spec --recommend --resume` without ID or spec",
    "`--recommend` with multiple spec arguments",
    "`/implement-phase --recommend`",
    "`--recommend` with `--dry-run`, `--draft`, `--no-split`, `--skip-gate`, or `--no-tag`",
):
    outcome = implement_rows.get(invocation, "")
    mutation_sentinel = not outcome.startswith("Reject")
    emit("implement-reject-before-mutation-" + str(len(invocation)) + "-" + invocation.split()[0].strip("`/"), outcome.startswith("Reject") and not mutation_sentinel, f"{invocation} must reject before the mutation sentinel")

emit(
    "create-fail-before-mutation",
    0 <= create.find("Validate the complete invocation") < create.find("### Recommended Contract and Package Branch"),
    "create-spec invocation validation must precede the first recommended mutation phase",
)
emit(
    "implement-fail-before-mutation",
    0 <= implement.find("Validate the entire row") < implement.find("### Complete Locked Package Preflight"),
    "implement-spec invocation validation must precede state/package mutation",
)

context_fields = {
    "execution_id", "state_path", "spec_path", "mode", "propagation_token",
    "parent_command", "return_contract", "package_manifest_sha256",
}
for name, text, anchor in (
    ("create", create, "invoke `/implement-spec` internally"),
    ("implement", implement, "accepts the parent's `delivery_context`"),
):
    try:
        block = fenced_after(text, anchor, "yaml")
        found = {line.strip().split(":", 1)[0] for line in block.splitlines() if line.startswith("  ") and ":" in line}
        emit(f"{name}-delivery-context", context_fields <= found, f"{name} delivery_context is missing {sorted(context_fields - found)}")
    except ValueError as exc:
        emit(f"{name}-delivery-context", False, str(exc))

emit(
    "negative-context-mismatch",
    "`delivery_context_mismatch`" in implement and "Never silently create a second execution" in implement,
    "mismatched propagated context must block without creating replacement state",
)
emit(
    "normal-mode-isolation",
    create.find("Normal branch (authoritative)") < create.find("### Authoritative `--recommend` Invocation Matrix")
    and implement.find("Normal branch (authoritative)") < implement.find("### Authoritative `--recommend` Invocation Matrix")
    and "Normal mode never discovers or resumes" in implement,
    "normal behavior must branch before and remain isolated from recommended state",
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
emit(
    "interrupted-worktree-adoption",
    "exactly one matching linked worktree" in implement and "must not relaunch stranded active work" in implement,
    "resume must adopt one matching active worktree instead of relaunching it",
)
emit(
    "worktree-ambiguity-blocks",
    "multiple matching worktrees" in implement and "worktree_identity_contradiction" in implement,
    "ambiguous and contradictory worktree identity must block explicitly",
)

emit(
    "failed-normalizes-blocked",
    "`failed`, malformed, missing, or mismatched outcomes normalize to classified" in implement
    and "`blocked`; dependents do not run." in implement,
    "nested failed outcomes must deterministically normalize to blocked",
)
try:
    result_block = fenced_after(implement, "After all stories reconcile as successful", "yaml")
except ValueError:
    result_block = ""
required_answer_lines = (
    "required_answer:",
    "  decision_id:",
    "  question_id:",
    "  option_ids:",
    "  selected_option_id:",
    "  resume_transition:",
    "  interaction_id:",
)
emit(
    "required-answer-return-identity",
    all(line in result_block for line in required_answer_lines),
    "implement-spec normative return schema lacks complete required_answer identity",
)
emit(
    "create-parent-answer-preservation",
    all(token in create for token in ("decision ID", "question ID", "option IDs", "same transition")),
    "create-spec parent boundary must preserve canonical answer identity",
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

def fixture(name):
    repo = workspace / name / "repo"
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
  require_literal "$preamble" 'Only a command invocation that explicitly documents `--recommend` may continue' "The preamble must preserve the default planning stop boundary."

  require_literal "$create_spec" 'Parse `--recommend` exactly once at command entry.' "Create-spec must parse recommendation mode once at entry."
  require_literal "$create_spec" 'Normal branch (authoritative): when `--recommend` is absent, follow every existing phase, prompt, terminal constraint, and next-step behavior below verbatim.' "Create-spec must preserve normal behavior behind an explicit branch."
  require_literal "$create_spec" '### Authoritative `--recommend` Invocation Matrix' "Create-spec must define its fail-before-mutation invocation matrix."
  require_literal "$create_spec" '`/create-spec --recommend --from-issue <one-path>`' "Create-spec must support one issue source in recommendation mode."
  require_literal "$create_spec" '`/create-spec --recommend --from-prototype`' "Create-spec must support prototype source in recommendation mode."
  require_literal "$create_spec" '`/create-spec --recommend --quick`' "Create-spec must reject recommend plus quick."
  require_literal "$create_spec" '`/create-spec --recommend --force`' "Create-spec must reject recommend plus force."
  require_literal "$create_spec" 'multiple source modes' "Create-spec must reject multiple source modes."
  require_literal "$create_spec" 'Before creating execution state or mutating any source issue' "Create-spec must validate invocation and package before state/source mutation."
  require_literal "$create_spec" 'recommendation-log.md' "Create-spec must create the tracked recommendation audit before implementation."
  require_literal "$create_spec" 'package_manifest_sha256' "Create-spec must pass a deterministic package manifest digest."
  require_literal "$create_spec" 'delivery_context' "Create-spec must propagate an explicit delivery context."
  require_literal "$create_spec" 'recommend-command-result-v1' "Create-spec must require the structured nested result contract."

  require_literal "$implement_spec" 'Parse `--recommend` exactly once at command entry.' "Implement-spec must parse recommendation mode once at entry."
  require_literal "$implement_spec" 'Normal branch (authoritative): when `--recommend` is absent, follow Phases 1–4 and Resume Support below verbatim.' "Implement-spec must preserve its existing normal workflow."
  require_literal "$implement_spec" '### Authoritative `--recommend` Invocation Matrix' "Implement-spec must define its fail-before-mutation invocation matrix."
  require_literal "$implement_spec" '`/implement-spec --recommend <one-spec>`' "Implement-spec must support direct existing-spec recommendation mode."
  require_literal "$implement_spec" '`/implement-spec --recommend --quick`' "Implement-spec must reject recommend plus quick."
  require_literal "$implement_spec" '`/implement-spec --recommend --force`' "Implement-spec must reject recommend plus force."
  require_literal "$implement_spec" '`/implement-spec --recommend --from <story>`' "Implement-spec must reject unsafe partial-DAG recommendation mode."
  require_literal "$implement_spec" 'multiple spec arguments' "Implement-spec must reject multiple specs."
  require_literal "$implement_spec" '`/implement-phase --recommend`' "Implement-spec must preserve the multi-spec exclusion."
  require_literal "$implement_spec" 'Normal mode never discovers or resumes `recommend-execution-*.json` state' "Normal mode must not silently resume recommended state."
  require_literal "$implement_spec" 'Complete Locked Package Preflight' "Implement-spec must validate the complete locked package before implementation."
  require_literal "$implement_spec" 'No unresolved `[UNPLANNED]`' "Implement-spec must reject unresolved technical operations."
  require_literal "$implement_spec" '### Read-Only Resume Reconciliation' "Recommended resume must reconcile repository reality before mutation."
  require_literal "$implement_spec" 'WWB incompleteness is a warning only' "Missing WWB details must not contradict implement-story degradation semantics."
  require_literal "$implement_spec" 'recommend-command-result-v1' "Implement-spec must normalize nested and final structured outcomes."
  require_literal "$implement_spec" 'verified_implementation' "Implement-spec must return a verified-implementation outcome."
  require_literal "$implement_spec" 'After verified implementation' "Story 4 must continue only after Story 3 verified implementation."
  require_literal "$implement_spec" 'scripts/recommend-state.py reserve-worktree' "Implement-spec must durably reserve worktree ownership before Gate 1."
  require_literal "$implement_story" '### Step 2.5: Recommended Worktree Launch Handshake' "Implement-story must expose the recommended launch handshake."
  require_literal "$implement_story" '`recommend-worktree-reservation-ack-v1`' "Gate 1 must require persisted parent acknowledgment."
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

  for adapter in "$cursor_adapter" "$claude_adapter" "$codex_adapter"; do
    require_literal "$adapter" '### Recommended Delivery Context and Resume' "Each adapter must map durable recommendation orchestration."
    require_literal "$adapter" '`delivery_context`' "Each adapter must transport the canonical delivery context."
    require_literal "$adapter" '`recommend-command-result-v1`' "Each adapter must return structured nested results."
    require_literal "$adapter" 'preserve stable question and option IDs' "Each adapter must preserve required-answer identity."
    require_literal "$adapter" 'validated sibling' "Each adapter must map crash-safe replacement."
    require_literal "$adapter" 'repository-only' "Each adapter must keep Story 3 reconciliation provider-free."
    require_literal "$adapter" '`recommend-worktree-launch-v1`' "Each adapter must map launch identity before Gate 1."
    require_literal "$adapter" '`recommend-worktree-reservation-ack-v1`' "Each adapter must require durable reservation acknowledgment."
    require_literal "$adapter" 'Story 3 repository-only reconciliation remains provider-free.' "Adapters must preserve Story 3's provider-free boundary."
  done
}

check_recommended_staging() {
  local helper="$PROJECT_ROOT/scripts/recommend-state.py"
  local fake="$PROJECT_ROOT/scripts/eval-recommend-stage.py"
  local state_doc="$PROJECT_ROOT/.writ/docs/recommended-delivery-state-format.md"
  local create_spec="$PROJECT_ROOT/commands/create-spec.md"
  local implement_spec="$PROJECT_ROOT/commands/implement-spec.md"
  local ship="$PROJECT_ROOT/commands/ship.md"
  local uat="$PROJECT_ROOT/commands/create-uat-plan.md"
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
  require_literal "$create_spec" 'staged Story 4 result' "Create-spec must continue to staged Story 4 output."
  require_literal "$implement_spec" '`findPullRequest`, `createPullRequest`, `getPullRequest`' "Implement-spec must use neutral PR operations."
  require_literal "$implement_spec" 'Silence stays `awaiting_approval`' "Silence must never approve production."
  require_literal "$ship" '`/ship --test --recommend`' "Recommended ship must require test semantics."
  require_literal "$uat" 'implementation_source_digest_sha256' "Recommended UAT must expose a deterministic source digest."
  for key in "Delivery Provider" "Delivery Remote" "Preview Provider" "Preview Project" "Preview Evidence Source" "Preview URL Pattern" "Required Checks" "CI Wait Timeout" "Preview Wait Timeout"; do
    require_literal "$config" "\`$key\`" "Config documentation must define $key."
  done

  for adapter in "$PROJECT_ROOT/adapters/cursor.md" "$PROJECT_ROOT/adapters/claude-code.md" "$PROJECT_ROOT/adapters/codex.md"; do
    require_literal "$adapter" '`findPullRequest`' "Each adapter must map PR lookup."
    require_literal "$adapter" '`listRequiredChecks`' "Each adapter must map required-check discovery."
    require_literal "$adapter" '`findPreview`' "Each adapter must map preview discovery."
    require_literal "$adapter" '`attempted`' "Each adapter must persist the PR mutation marker."
    require_literal "$adapter" 'provenance' "Each adapter must return observable preview provenance."
    require_literal "$adapter" 'snapshot digest' "Each adapter must return fresh approval reconciliation."
    require_literal "$adapter" '`previewProjectId`' "Each adapter must normalize Preview Project."
    require_literal "$adapter" '`authenticated: true`' "Each adapter must prove required-check authentication."
    require_literal "$adapter" 'No browser automation' "Each adapter must prohibit browser automation."
    forbid_literal "$adapter" 'mergePullRequest' "Story 4 adapters must not expose merge operations."
  done

  forbid_literal "$helper" 'deploy_to_vercel' "The local reducer must not deploy previews."
  forbid_literal "$helper" 'browser_navigate' "The local reducer must not automate browsers."
  forbid_literal "$helper" 'import requests' "The local reducer must not call provider HTTP APIs."
  forbid_literal "$helper" 'urllib.request' "The local reducer must not call provider HTTP APIs."
  forbid_literal "$implement_spec" 'npm publish' "Recommended staging must not publish packages."
}

run_check() {
  local check="$1"
  local func="check_${check//-/_}"

  CURRENT_CHECK="$check"
  CURRENT_FINDINGS=0
  CURRENT_SCENARIOS=0
  CURRENT_SCENARIOS_PASSED=0
  CURRENT_STATIC_ASSERTIONS=0
  CURRENT_STATIC_ASSERTIONS_PASSED=0
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
    if [ "$CURRENT_SCENARIOS" -gt 0 ]; then
      echo ""
      echo "Scenarios: $CURRENT_SCENARIOS_PASSED/$CURRENT_SCENARIOS passed"
    fi
    if [ "$CURRENT_STATIC_ASSERTIONS" -gt 0 ]; then
      echo "Supplementary static assertions: $CURRENT_STATIC_ASSERTIONS_PASSED/$CURRENT_STATIC_ASSERTIONS passed"
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

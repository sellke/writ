#!/usr/bin/env bash
# Migration check for ADR-024 Story 2 (spec 2026-09-03-model-delegation):
# the eight agents, the manifest, and the two scaffolders sit on the
# anchor/floor vocabulary with no hardcoded "fast" and no advisory carrier.
#
# Asserts (AC-2.1 .. AC-2.5):
#   (a) `model_tier:` appears exactly 8 times under agents/, one per file, with
#       the value the spec's "Tier derivation applied" table assigns by name;
#       visual-qa-agent.md keeps its value inside the yaml fence (no `---`)
#   (b) no `"fast"` and no `model_tier: capability` under agents/;
#       no `model_tier` anywhere under commands/ or skills/
#   (c) every manifest agent entry's model_tier equals its agent file's and
#       no manifest agent entry carries a `model:` key
#   (d) commands/new-command.md scaffolds `entry_level: <high|standard|any>`
#   (e) lint-skill.sh emits zero deprecated-alias warnings for agents/ and
#       the manifest (exit code alone is not evidence: aliases exit 0)
#   (f) gen-skill.sh renders a `Tier` column, no `Model` column, and --check
#       exits 0 against the committed SKILL.md
#   Templates: each of the six Task({...}) templates carries exactly one
#       adapter-resolution comment in place of `model: "fast"`.
#
# Every assertion is anchored on `model_tier:` / `model_tier` literals, never on
# bare `anchor`/`floor`/`orchestration`/`capability`: coding-agent.md uses
# "orchestration" as prose and the manifest says "capability files".
# Assertions use grep, not rg (eval.sh has zero rg calls; keep it portable).
set -uo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO"

FAILURES=0
fail() {
  printf 'FAIL: %s\n' "$1" >&2
  FAILURES=$((FAILURES + 1))
}

ltrim() {
  local value="$1"
  printf '%s' "${value#"${value%%[![:space:]]*}"}"
}

# Spec authority: spec.md -> "Tier derivation applied". Two parallel lists
# (macOS bash 3.2 has no associative arrays).
AGENT_NAMES=(coding-agent review-agent testing-agent visual-qa-agent documentation-agent evaluator-agent architecture-check-agent user-story-generator)
AGENT_TIERS=(anchor       anchor       anchor        anchor          anchor              anchor          floor                    floor)

expected_tier_for() {  # $1 agent name -> prints tier or nothing
  local i
  for ((i = 0; i < ${#AGENT_NAMES[@]}; i++)); do
    if [ "${AGENT_NAMES[$i]}" = "$1" ]; then
      printf '%s' "${AGENT_TIERS[$i]}"
      return 0
    fi
  done
  return 1
}

# ----- (a) eight declarations, by name, from the derivation table -----
total=$(grep -rn 'model_tier:' agents/ | wc -l | tr -d ' ')
[ "$total" = 8 ] || fail "(a) expected exactly 8 'model_tier:' hits under agents/, got $total"

for ((i = 0; i < ${#AGENT_NAMES[@]}; i++)); do
  name="${AGENT_NAMES[$i]}"
  tier="${AGENT_TIERS[$i]}"
  n=$(grep -c "^model_tier: ${tier}\$" "agents/${name}.md" || true)
  [ "$n" = 1 ] || fail "(a) agents/${name}.md must declare 'model_tier: ${tier}' exactly once (found $n)"
done

[ "$(head -n 1 agents/visual-qa-agent.md)" != "---" ] \
  || fail "(a) visual-qa-agent.md must not gain a --- frontmatter header; the value lives in its yaml fence"

# ----- (b) "fast" retired; no advisory carrier on commands or skills -----
if grep -rEn '"fast"|model_tier: capability' agents/ >/dev/null; then
  fail "(b) agents/ still contains \"fast\" or 'model_tier: capability':
$(grep -rEn '"fast"|model_tier: capability' agents/)"
fi
if grep -rn 'model_tier' commands/ skills/ >/dev/null; then
  fail "(b) commands/ or skills/ still mention model_tier:
$(grep -rn 'model_tier' commands/ skills/)"
fi

# ----- templates: one adapter-resolution comment each, no model: line -----
for spec in "architecture-check-agent:1" "user-story-generator:5"; do
  name="${spec%%:*}"
  want="${spec##*:}"
  n=$(grep -c 'adapter-resolved' "agents/${name}.md" || true)
  [ "$n" = "$want" ] || fail "(templates) agents/${name}.md must carry exactly $want adapter-resolution comment(s), found $n"
  # The Agent Configuration block of a floor agent has no model: line.
  if awk '/^## Agent Configuration/{f=1} f && /^```$/{c++} f && c==2{exit} f' "agents/${name}.md" | grep -q '^model:'; then
    fail "(templates) agents/${name}.md Agent Configuration block still has a model: line"
  fi
done

# ----- (c) manifest agent entries mirror the agent files; no model: key -----
manifest_agents_block() {
  # Indented lines between `agents:` and the next column-0 line (key or comment).
  awk '/^agents:/{f=1; next} f && /^[^ ]/{exit} f' .writ/manifest.yaml
}

entry=""
seen=0
while IFS= read -r raw; do
  line="$(ltrim "$raw")"
  case "$line" in
    "- name:"*)
      entry="$(ltrim "${line#- name:}")"
      seen=$((seen + 1))
      ;;
    "model_tier:"*)
      value="$(ltrim "${line#model_tier:}")"
      want="$(expected_tier_for "$entry" || true)"
      [ -n "$want" ] || fail "(c) manifest agent '$entry' is not in the derivation table"
      [ "$value" = "$want" ] || fail "(c) manifest agent '$entry' has model_tier '$value', agent file/table says '$want'"
      ;;
    "model:"*)
      fail "(c) manifest agent '$entry' still carries a model: key ('$line')"
      ;;
  esac
done < <(manifest_agents_block)
[ "$seen" = 8 ] || fail "(c) expected 8 manifest agent entries, parsed $seen"
tiers_in_manifest=$(manifest_agents_block | grep -c 'model_tier:' || true)
[ "$tiers_in_manifest" = 8 ] || fail "(c) expected 8 model_tier lines in the manifest agents block, got $tiers_in_manifest"

# ----- (d) /new-command scaffolds entry_level -----
n=$(grep -c 'entry_level:' commands/new-command.md || true)
[ "$n" -ge 1 ] || fail "(d) commands/new-command.md must mention 'entry_level:' at least once"
grep -qF 'entry_level: <high|standard|any>' commands/new-command.md \
  || fail "(d) commands/new-command.md must scaffold the literal 'entry_level: <high|standard|any>'"

# ----- (e) zero deprecated-alias warnings from agents/ and the manifest -----
# lint-skill.sh is a SKILL.md lint and exits 1 on agent files for unrelated
# description/lifecycle findings; only the alias count is evidence here.
alias_warnings=$( { bash scripts/lint-skill.sh agents/*.md .writ/manifest.yaml 2>&1 || true; } | grep -c 'deprecated alias' || true)
[ "$alias_warnings" = 0 ] || fail "(e) lint-skill.sh emitted $alias_warnings deprecated-alias warning(s) for agents/ or the manifest"

# ----- (f) generator renders Tier, not Model, and SKILL.md is current -----
dry=$(bash scripts/gen-skill.sh --dry-run 2>/dev/null) \
  || fail "(f) gen-skill.sh --dry-run failed (manifest without model: must still generate)"
printf '%s\n' "$dry" | grep -qF '| Agent | File | Tier | Purpose |' \
  || fail "(f) SKILL.md Available Agents table must have a Tier column"
if printf '%s\n' "$dry" | grep -qF '| Model |'; then
  fail "(f) SKILL.md Available Agents table must not render a Model column"
fi
bash scripts/gen-skill.sh --check >/dev/null 2>&1 \
  || fail "(f) gen-skill.sh --check must exit 0 against the regenerated SKILL.md"

if [ "$FAILURES" -gt 0 ]; then
  printf '%d assertion(s) failed\n' "$FAILURES" >&2
  exit 1
fi
printf 'OK model_tier migration (8 agents, manifest, scaffolders, generator)\n'

#!/usr/bin/env bash
# Cross-check agents/*.md vs claude-code/agents and codex/agents counterparts,
# then check the generated content with each generator's --check.
#
# Usage: bash scripts/check-agent-parity.sh [--help]
#
# Prints the agent CLI contract's check shape (.writ/docs/agent-cli-contract.md):
#   line 1  pass | fail | unverifiable
#   then    one `reason:` line per missing counterpart or content drift
#   last    check-agent-parity: <verdict> (...)
#
# Content check: after the presence loop the script runs
# `python3 scripts/<gen> --check` for gen-claude-agents.py and
# gen-codex-agent-tomls.py. Each `reason: <kind> <stem>` line becomes the drift
# reason `<gen>: <kind> <stem>`; an exit code of 2 or more becomes
# `<gen> --check exited <rc>`. A generator absent beside this script (temp-copy
# tests) is skipped, and the summary ends with `; content not checked: <gens>`.
#
# Exit 0 on pass or unverifiable (no agents/ folder), 1 on fail (drift),
# 2 on a usage error (any argument but --help; usage on stderr). Drift is a
# warning to /refresh-command --check-parity: the caller reads line 1 and
# never blocks on `fail`.

set -uo pipefail

usage() {
  echo "Usage: bash scripts/check-agent-parity.sh [--help]"
  echo ""
  echo "Warns when an agents/*.md file has no claude-code/agents/ or codex/agents/"
  echo "counterpart, or when generated content drifts from gen-claude-agents.py or"
  echo "gen-codex-agent-tomls.py --check. Line 1 is pass, fail, or unverifiable; one"
  echo "reason: line per problem; a check-agent-parity: summary is last."
  echo "Exit 0 pass or unverifiable, 1 fail (drift), 2 usage error."
}

case "${1:-}" in
  "") ;;
  --help|-h) usage; exit 0 ;;
  *) echo "check-agent-parity: unexpected argument: $1" >&2; usage >&2; exit 2 ;;
esac
if [ $# -gt 1 ]; then
  echo "check-agent-parity: unexpected argument: $2" >&2
  usage >&2
  exit 2
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [[ ! -d "$ROOT/agents" ]]; then
  echo "unverifiable"
  echo "reason: no agents/ folder at $ROOT"
  echo "check-agent-parity: unverifiable (no agents/ folder)"
  exit 0
fi

claude_counterpart() {
  case "$1" in
    architecture-check-agent) echo "writ-architect.md" ;;
    coding-agent) echo "writ-coder.md" ;;
    documentation-agent) echo "writ-documenter.md" ;;
    evaluator-agent) echo "writ-evaluator.md" ;;
    review-agent) echo "writ-reviewer.md" ;;
    testing-agent) echo "writ-tester.md" ;;
    user-story-generator) echo "writ-story-gen.md" ;;
    visual-qa-agent) echo "writ-visual-qa.md" ;;
    *) echo "" ;;
  esac
}

REASONS=""
DRIFT=0
MISSING=0
CONTENT=0
AGENTS=0
SKIPPED=""
drift() {
  REASONS="${REASONS}reason: $1"$'\n'
  DRIFT=$((DRIFT + 1))
}

shopt -s nullglob
for md in "$ROOT/agents"/*.md; do
  [[ -f "$md" ]] || continue
  stem=$(basename "$md" .md)
  AGENTS=$((AGENTS + 1))

  if [[ ! -f "$ROOT/codex/agents/${stem}.toml" ]]; then
    drift "agents/${stem}.md has no counterpart in codex/agents/"
    MISSING=$((MISSING + 1))
  fi

  cf=$(claude_counterpart "$stem")
  if [[ -z "$cf" || ! -f "$ROOT/claude-code/agents/$cf" ]]; then
    drift "agents/${stem}.md has no counterpart in claude-code/agents/"
    MISSING=$((MISSING + 1))
  fi
done

for gen in gen-claude-agents.py gen-codex-agent-tomls.py; do
  if [[ ! -f "$ROOT/scripts/$gen" ]]; then
    SKIPPED="${SKIPPED:+$SKIPPED }$gen"
    continue
  fi
  rc=0
  found=0
  out=$(python3 "$ROOT/scripts/$gen" --check 2>&1) || rc=$?
  if [[ "$rc" -ge 2 ]]; then
    drift "$gen --check exited $rc"
    CONTENT=$((CONTENT + 1))
    continue
  fi
  while IFS= read -r line; do
    case "$line" in
      "reason: "*)
        drift "$gen: ${line#reason: }"
        CONTENT=$((CONTENT + 1))
        found=$((found + 1))
        ;;
    esac
  done <<< "$out"
  if [[ "$rc" -eq 1 && "$found" -eq 0 ]]; then
    drift "$gen --check failed without a reason line"
    CONTENT=$((CONTENT + 1))
  fi
done

NOTE=""
if [[ -n "$SKIPPED" ]]; then
  NOTE="; content not checked: $SKIPPED"
fi

if [[ "$DRIFT" -eq 0 ]]; then
  echo "pass"
  echo "check-agent-parity: pass ($AGENTS agents; agents/, claude-code/agents/, and codex/agents/ aligned${NOTE})"
  exit 0
fi

echo "fail"
printf '%s' "$REASONS"
echo "check-agent-parity: fail ($MISSING missing counterpart(s), $CONTENT content drift reason(s) across $AGENTS agents${NOTE})"
exit 1

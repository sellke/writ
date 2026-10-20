#!/usr/bin/env bash
# Cross-check agents/*.md vs claude-code/agents and codex/agents counterparts.
#
# Usage: bash scripts/check-agent-parity.sh [--help]
#
# Prints the agent CLI contract's check shape (.writ/docs/agent-cli-contract.md):
#   line 1  pass | fail | unverifiable
#   then    one `reason:` line per missing counterpart
#   last    check-agent-parity: <verdict> (...)
#
# Exit 0 on pass or unverifiable (no agents/ folder), 1 on fail (drift),
# 2 on a usage error (any argument but --help; usage on stderr). Drift is a
# warning to /refresh-command --check-parity: the caller reads line 1 and
# never blocks on `fail`.
#
# Exclusions (documented in commands/refresh-command.md):
#   - visual-qa-agent has no claude-code/agents/writ-*.md peer by design.

set -uo pipefail

usage() {
  echo "Usage: bash scripts/check-agent-parity.sh [--help]"
  echo ""
  echo "Warns when an agents/*.md file has no claude-code/agents/ or codex/agents/"
  echo "counterpart. Line 1 is pass, fail, or unverifiable; one reason: line per"
  echo "missing counterpart; a check-agent-parity: summary is last."
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
    *) echo "" ;;
  esac
}

claude_exempt() {
  [[ "$1" == "visual-qa-agent" ]]
}

REASONS=""
DRIFT=0
AGENTS=0
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
  fi

  if claude_exempt "$stem"; then
    continue
  fi

  cf=$(claude_counterpart "$stem")
  if [[ -z "$cf" || ! -f "$ROOT/claude-code/agents/$cf" ]]; then
    drift "agents/${stem}.md has no counterpart in claude-code/agents/"
  fi
done

if [[ "$DRIFT" -eq 0 ]]; then
  echo "pass"
  echo "check-agent-parity: pass ($AGENTS agents; agents/, claude-code/agents/, and codex/agents/ aligned, subject to documented exclusions)"
  exit 0
fi

echo "fail"
printf '%s' "$REASONS"
echo "check-agent-parity: fail ($DRIFT missing counterpart(s) across $AGENTS agents)"
exit 1

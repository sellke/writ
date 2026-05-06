#!/usr/bin/env bash
# Cross-check agents/*.md vs claude-code/agents and codex/agents counterparts.
# Warnings only — always exits 0 (per /refresh-command --check-parity contract).
#
# Usage: bash scripts/check-agent-parity.sh
#
# Exclusions (documented in commands/refresh-command.md):
#   - visual-qa-agent has no claude-code/agents/writ-*.md peer by design.

set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WARNINGS=0

claude_counterpart() {
  case "$1" in
    architecture-check-agent) echo "writ-architect.md" ;;
    coding-agent) echo "writ-coder.md" ;;
    documentation-agent) echo "writ-documenter.md" ;;
    review-agent) echo "writ-reviewer.md" ;;
    testing-agent) echo "writ-tester.md" ;;
    user-story-generator) echo "writ-story-gen.md" ;;
    *) echo "" ;;
  esac
}

claude_exempt() {
  [[ "$1" == "visual-qa-agent" ]]
}

shopt -s nullglob
for md in "$ROOT/agents"/*.md; do
  [[ -f "$md" ]] || continue
  stem=$(basename "$md" .md)

  if [[ ! -f "$ROOT/codex/agents/${stem}.toml" ]]; then
    echo "⚠️ agents/${stem}.md has no counterpart in codex/agents/"
    WARNINGS=$((WARNINGS + 1))
  fi

  if claude_exempt "$stem"; then
    continue
  fi

  cf=$(claude_counterpart "$stem")
  if [[ -z "$cf" || ! -f "$ROOT/claude-code/agents/$cf" ]]; then
    echo "⚠️ agents/${stem}.md has no counterpart in claude-code/agents/"
    WARNINGS=$((WARNINGS + 1))
  fi
done

if [[ "$WARNINGS" -eq 0 ]]; then
  echo "parity OK — agents/, claude-code/agents/, and codex/agents/ aligned (subject to documented exclusions)"
fi

exit 0

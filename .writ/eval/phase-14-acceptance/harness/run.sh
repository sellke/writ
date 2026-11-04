#!/bin/bash
# run.sh <condition> <run-name> <prompt> [extra CLI args...]
# Resets the condition's workspace to its committed state, runs one headless
# session, and saves the raw event stream plus a git status after the run.
set -uo pipefail
S=<scratchpad>
R=$(cat $S/root.txt); cond=$1; name=$2; prompt=$3; shift 3
ws=$R/ws/${WS:-$cond}; out=$R/runs/$cond; mkdir -p $out
cd $ws || exit 2
git checkout -q -- . && git clean -qfd -e .claude/settings.local.json
case $cond in
  claude-*)
    claude -p "$prompt" --output-format stream-json --verbose --setting-sources project,local \
      --no-session-persistence "$@" > $out/$name.jsonl 2> $out/$name.err < /dev/null ;;
  codex-*)
    codex exec --ignore-user-config -m gpt-6-astra -c model_reasoning_effort=medium --json \
      --skip-git-repo-check "$@" "$prompt" > $out/$name.jsonl 2> $out/$name.err < /dev/null ;;
esac
echo "exit=$?" > $out/$name.meta
git status --short --untracked-files=all > $out/$name.status

#!/bin/bash
# run2.sh <condition> <run-name> <prompt1> <prompt2> [extra CLI args...]
# Two-turn session: turn 2 resumes turn 1's session. Workspace from $WS (default: condition).
set -uo pipefail
S=<scratchpad>
R=$(cat $S/root.txt); cond=$1; name=$2; p1=$3; p2=$4; shift 4
ws=$R/ws/${WS:-$cond}; out=$R/runs/$cond; mkdir -p $out
cd $ws || exit 2
git checkout -q -- . && git clean -qfd -e .claude/settings.local.json
case $cond in
  claude-*)
    claude -p "$p1" --output-format stream-json --verbose --setting-sources project,local "$@" > $out/$name.t1.jsonl 2> $out/$name.err < /dev/null
    sid=$(python3 -c "import json,sys; [print(json.loads(l)['session_id']) for l in open('$out/$name.t1.jsonl') if '\"type\":\"result\"' in l]" | tail -1)
    claude -p "$p2" --resume "$sid" --output-format stream-json --verbose --setting-sources project,local "$@" > $out/$name.t2.jsonl 2>> $out/$name.err < /dev/null ;;
  codex-*)
    codex exec --ignore-user-config -m gpt-6-astra -c model_reasoning_effort=medium --json --skip-git-repo-check -s workspace-write "$p1" > $out/$name.t1.jsonl 2> $out/$name.err < /dev/null
    sid=$(python3 -c "import json; [print(json.loads(l)['thread_id']) for l in open('$out/$name.t1.jsonl') if '\"thread.started\"' in l]" | head -1)
    codex exec resume --ignore-user-config -m gpt-6-astra -c model_reasoning_effort=medium -c sandbox_mode=workspace-write --json --skip-git-repo-check "$sid" "$p2" > $out/$name.t2.jsonl 2>> $out/$name.err < /dev/null ;;
esac
{ echo '{"type":"turn_marker","turn":1}'; cat $out/$name.t1.jsonl; echo '{"type":"turn_marker","turn":2}'; cat $out/$name.t2.jsonl; } > $out/$name.jsonl
echo "sid=$sid" > $out/$name.meta
git status --short --untracked-files=all > $out/$name.status

#!/bin/bash
# run.sh <condition> <probe> <n> : one Codex run in a fresh copy of the condition's
# installed app, under an opaque directory name. Needs R from setup.sh.
set -uo pipefail
H=$(cd "$(dirname "$0")" && pwd)
: "${R:?set R to the root setup.sh printed}"
cond=$1; probe=$2; n=$3
id=$(python3 -c 'import secrets; print(secrets.token_hex(4))')
cp -R "$R/apps/$cond" "$R/w/$id"
echo "$id $cond $probe $n" >> "$R/map.txt"
out=$R/runs/$id; mkdir -p "$out"
cd "$R/w/$id" || exit 2
codex exec --ignore-user-config -m gpt-6-astra -c model_reasoning_effort=medium -s read-only \
  --json --skip-git-repo-check "$(cat "$H/$probe.txt")" > "$out/run.jsonl" 2> "$out/err.txt" < /dev/null
echo "exit=$?" > "$out/meta.txt"
git status --short --untracked-files=all > "$out/status.txt"

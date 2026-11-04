#!/bin/bash
S=<scratchpad>; R=$(cat $S/root.txt)
REQ="get('page_size', {'page_size': 0}) should raise ValueError for a page size below 1."
for n in 1 2 3; do
  (cd $R/ws/claude-g5fix && git worktree list | tail -n +2 | awk '{print $1}' | xargs -I{} git worktree remove --force {} 2>/dev/null; git worktree prune; git branch | grep -v '^\*' | xargs -I{} git branch -D {} >/dev/null 2>&1)
  $S/run2.sh claude-g5fix g5fix-$n "/writ:writ \"$REQ\"" "1" --max-turns 30 --permission-mode acceptEdits --allowedTools Bash --plugin-dir $R/src-fix2/plugins/writ
  (cd $R/ws/claude-g5fix && uv run --quiet --with pytest python -m pytest -q > $R/runs/claude-g5fix/g5fix-$n.pytest 2>&1; echo "pytest_exit=$?" >> $R/runs/claude-g5fix/g5fix-$n.pytest; git diff > $R/runs/claude-g5fix/g5fix-$n.diff; git worktree list > $R/runs/claude-g5fix/g5fix-$n.worktrees)
done; echo g5fix-done

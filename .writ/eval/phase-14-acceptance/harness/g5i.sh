#!/bin/bash
S=<scratchpad>; R=$(cat $S/root.txt)
REQ="get('page_size', {'page_size': 0}) should raise ValueError for a page size below 1."
for n in 1 2 3; do
  (cd $R/ws/claude-g5i && git worktree list | tail -n +2 | awk '{print $1}' | xargs -I{} git worktree remove --force {} 2>/dev/null; git worktree prune)
  $S/run2.sh claude-g5i g5i-$n "/writ \"$REQ\"" "1" --max-turns 30 --permission-mode acceptEdits --allowedTools Bash
  (cd $R/ws/claude-g5i && uv run --quiet --with pytest python -m pytest -q > $R/runs/claude-g5i/g5i-$n.pytest 2>&1; echo "pytest_exit=$?" >> $R/runs/claude-g5i/g5i-$n.pytest; git diff > $R/runs/claude-g5i/g5i-$n.diff; git worktree list > $R/runs/claude-g5i/g5i-$n.worktrees)
done; echo g5i-done

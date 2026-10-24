#!/bin/bash
S=<scratchpad>; R=$(cat $S/root.txt)
REQ="get('page_size', {'page_size': 0}) should raise ValueError for a page size below 1."
plughash() { { (cd $R/src-rc/plugins/writ && find . -type f -print0 | sort -z | xargs -0 shasum -a 256); (cd ~/.claude/plugins/cache/writ/writ && find . -type f -print0 | sort -z | xargs -0 shasum -a 256); git -C $R/src-rc status --short; } | shasum -a 256 | cut -c1-16; }
for n in 1 2 3; do
  before=$(plughash)
  WS=claude-plugin $S/run2.sh claude-g5 g5-$n "/writ:writ \"$REQ\"" "1" --max-turns 30 --permission-mode acceptEdits --allowedTools Bash
  (cd $R/ws/claude-plugin && uv run --quiet --with pytest python -m pytest -q > $R/runs/claude-g5/g5-$n.pytest 2>&1; echo "pytest_exit=$?" >> $R/runs/claude-g5/g5-$n.pytest; git diff > $R/runs/claude-g5/g5-$n.diff)
  after=$(plughash); echo "plugin_hash_before=$before after=$after" >> $R/runs/claude-g5/g5-$n.meta
done; echo g5-done

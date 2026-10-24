#!/bin/bash
S=<scratchpad>; R=$(cat $S/root.txt)
RO=(--tools "Read,Glob,Grep,AskUserQuestion,TodoWrite")
REQ="get('page_size', {'page_size': 0}) should raise ValueError for a page size below 1."
P6="Using only this project's Writ instructions, name the tool or behavior the capability todo_write maps to on this platform, and the one AskQuestion maps to. Answer in two lines, then name the file or section you took them from."
plughash() { { (cd $R/src-rc/plugins/writ && find . -type f -print0 | sort -z | xargs -0 shasum -a 256); (cd ~/.claude/plugins/cache/writ/writ && find . -type f -print0 | sort -z | xargs -0 shasum -a 256); git -C $R/src-rc status --short; } | shasum -a 256 | cut -c1-16; }
( for n in 1 2 3; do $S/run2.sh claude-g1 g1-$n "The page_size default of 20 is too small for our tables. Don't change anything yet." "/writ" --max-turns 12 "${RO[@]}"; done ) &
( for n in 1 2 3; do $S/run2.sh claude-g2 g2-$n "/writ \"$REQ\"" "1" --max-turns 15 --tools "Read,Glob,Grep,AskUserQuestion,TodoWrite,Edit,Write,Bash" --permission-mode acceptEdits; done ) &
( for n in 1 2 3; do $S/run.sh claude-g3 g3-$n '/writ "Implement phase 14."' --max-turns 12 "${RO[@]}"; done ) &
( for n in 1 2 3; do $S/run2.sh codex-g4 g4-$n "Follow .codex/commands/writ.md for this request: $REQ" "Go with your recommended route."; done ) &
( for n in 1 2 3; do $S/run.sh claude-g6 g6-$n "$P6" --max-turns 6; $S/run.sh codex-g6 g6-$n "$P6" -s read-only; done ) &
( for n in 1 2 3; do $S/run.sh claude-g8 g8-$n "/create-spec \"a reset command that restores every setting to its default\"" --permission-mode plan --max-turns 20; done ) &
( for n in 1 2 3; do
    before=$(plughash)
    WS=claude-plugin $S/run2.sh claude-g5 g5-$n "/writ:writ \"$REQ\"" "1" --max-turns 30 --permission-mode acceptEdits --allowedTools Bash
    (cd $R/ws/claude-plugin && python3 -m pytest -q > $R/runs/claude-g5/g5-$n.pytest 2>&1; echo "pytest_exit=$?" >> $R/runs/claude-g5/g5-$n.pytest)
    after=$(plughash); echo "plugin_hash_before=$before after=$after" >> $R/runs/claude-g5/g5-$n.meta
  done
  cp $R/ws/claude-plugin/.claude/settings.local.json $S/plugin-settings.local.bak
  python3 - $R/ws/claude-plugin/.claude/settings.local.json <<'PY'
import json,sys; p=sys.argv[1]; d=json.load(open(p)); d["outputStyle"]="Explanatory"; json.dump(d,open(p,"w"),indent=2)
PY
  for n in 1 2 3; do WS=claude-plugin $S/run.sh claude-g7 g7-$n "$(cat $S/P1.txt)" --max-turns 8; done
  cp $S/plugin-settings.local.bak $R/ws/claude-plugin/.claude/settings.local.json ) &
wait; echo gaps-done

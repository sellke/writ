#!/bin/bash
S=<scratchpad>
SET=~/Projects/writ/.writ/eval/phase-14-acceptance/routing-set.json
python3 -c "import json; [print(i['id']+'\t'+i['request']) for i in json.load(open('$SET'))['items']]" > $S/routing-items.tsv
i=0
while IFS=$'\t' read -r id req; do
  k=$(( i % 4 + 1 )); i=$((i+1))
  echo "$k	$id	$req"
done < $S/routing-items.tsv > $S/routing-plan.tsv
for k in 1 2 3 4; do
  ( grep "^$k	" $S/routing-plan.tsv | grep -v -E "	(R01|R02|R03|R04)	" | while IFS=$'\t' read -r kk id req; do
      printf '%s\n' "/writ \"$req\"" > $S/prompt-$id.txt
      WS=claude-routing-$k $S/run.sh claude-routing $id "/writ \"$req\"" --max-turns 12 --tools "Read,Glob,Grep,AskUserQuestion,TodoWrite"
    done ) &
done; wait; echo routing-done

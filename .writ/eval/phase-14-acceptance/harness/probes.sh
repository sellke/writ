#!/bin/bash
S=<scratchpad>
P1=$(cat $S/P1.txt); P2=$(cat $S/P2.txt)
for c in claude-installsh claude-plugin claude-control codex-installsh codex-control; do
  ( for n in 1 2 3; do
      case $c in claude-*) X=(--max-turns 8);; codex-*) X=(-s read-only);; esac
      $S/run.sh $c identity-$n "$P1" "${X[@]}"; $S/run.sh $c verify-$n "$P2" "${X[@]}"
    done ) &
done; wait

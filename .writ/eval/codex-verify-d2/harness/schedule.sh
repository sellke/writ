#!/bin/bash
# schedule.sh : rubric.md -> Schedule. Round n runs every condition once, in parallel.
set -uo pipefail
H=$(cd "$(dirname "$0")" && pwd)
: "${R:?set R to the root setup.sh printed}"
ALL=(control base pd-first pd-last intro-op)
WRIT=(base pd-first pd-last intro-op)
round() { local probe=$1 n=$2; shift 2
  for c in "$@"; do "$H/run.sh" "$c" "$probe" "$n" & done; wait
  echo "$(date +%H:%M:%S) $probe round $n done"; }
for n in 1 2 3 4 5 6 7 8 9 10; do round P2 $n "${ALL[@]}"; done
for n in 1 2 3 4 5; do round P3 $n "${ALL[@]}"; done
for n in 1 2 3; do round P1 $n "${WRIT[@]}"; done

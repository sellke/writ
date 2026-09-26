## QUALITY

- Baseline exit-criteria pass rate on the yuss.app set after each cut is at or above the Stage 1 figure.
- `bash scripts/eval.sh` exits 0 at the end of every iteration.
- No file under `adapters/` gains more than one model-specific instruction line per model.

How to check DONE WHEN: run `python3 scripts/exit-criteria.py` against the spec named by spec_ref.

No `--recommend` command merges, opens PRs, or releases. Production remains a human decision.

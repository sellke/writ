# Technical Spec: `/refactor` Dirty-Tree Guard

## Measured current state (verified 2026-08-12)

- `grep -n "porcelain\|dirty" commands/refactor.md skills/safe-refactor-loop/SKILL.md` → **no matches**. The guard does not exist in either file.
- `commands/revert.md` carries the guard at lines 60-67 and names it Safety Guarantee #1 at :144.
- `skills/safe-refactor-loop/SKILL.md` step 1 reads "**Checkpoint** — note the current clean git state so a revert is one step" — an assumption, not a check.

## Edit surface

| File | Change | Story |
|---|---|---|
| `commands/refactor.md` | porcelain guard ahead of Step 1.2 | 1 |
| `skills/safe-refactor-loop/SKILL.md` | step 1 captures HEAD + asserts clean | 2 |

## Error & Rescue Map

| Situation | Behaviour |
|---|---|
| Tree dirty at invocation | HALT before any mutation; name the remedy (commit or stash) |
| Tree clean | No change — identical behaviour to today |
| `--dead-code` target untracked | Report and skip; no git object exists to restore from |
| Not a git repo | Degrade with a warning; do not HALT (mirrors existing tolerance) |

## Verification

- `bash scripts/eval.sh` → `Findings: 0`
- `bash scripts/lint-skill.sh skills/safe-refactor-loop/SKILL.md` → clean
- A clean-tree `/refactor` dry run behaves identically to pre-change.

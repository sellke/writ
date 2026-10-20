# Decide Where Shipped Scripts Install

> **Type:** Improvement
> **Priority:** Normal
> **Effort:** Medium
> **Created:** 2026-10-12
> **spec_ref:** _(set automatically when promoted via `/create-spec --from-issue`)_

## TL;DR

Decide whether Writ's shipped scripts should move out of the project-root `scripts/` folder, the way pstack keeps its tools inside the skill folder that uses them.

## Current State

- `install.sh` and `update.sh` copy every script `is_shippable_script` accepts into the project's root `scripts/` folder, beside the project's own scripts.
- ADR-029 lists this as a negative consequence: pstack keeps its tools in the skill folder (`skills/poteto-mode/scripts/`), so they never collide with a project's own `scripts/`, and Writ's layout can. The ADR put the fix out of scope and asked for this issue.
- A project file with the same name as a shipped script has no install baseline, so install keeps it as "assumed modified". Writ's commands then run the project's file under Writ's name. With `--force`, install overwrites the project's file instead.
- Commands, agents, skills, adapters, and `codex/` call scripts by the path `scripts/<name>`, so a move changes every caller.

## Expected Outcome

- A recorded decision (an ADR-029 amendment or a new ADR): keep `scripts/`, move to a Writ-owned folder such as `.writ/scripts/`, or keep each tool beside the skill or command that runs it.
- If the scripts move: install, update, and uninstall handle the new location; update migrates existing installs; every caller path changes in the same release; the contract test reads the shipped set from the new location.
- The decision says what happens to a project's own file that shares a name with a Writ script.

## Relevant Files

- `.writ/decision-records/adr-029-agent-cli-contract.md` - Consequences: "Scripts install into the project-root `scripts/` folder"
- `scripts/install.sh` - `is_shippable_script` and `overlay_scan_flat_dir`, which copy scripts into `scripts/`
- `.writ/docs/agent-cli-contract.md` - Scope names the `scripts/` folder

## Related Issues

- [2026-10-12-agent-facing-writ-cli](../features/2026-10-12-agent-facing-writ-cli.md) - origin; ADR-029 deferred this question here
- [2026-10-02-merge-customized-commands-on-update](2026-10-02-merge-customized-commands-on-update.md) - how update treats locally modified files

## Notes

- A move touches command files that carry byte pins (`scripts/tests/test_governor_enforcement.py`) and hash pins (`scripts/tests/test_lean_commands.py`).
- This repo dogfoods itself: `.cursor/` and `.claude/` symlink to product source, and `eval.sh` runs scripts from `scripts/`. A move must keep the source repo working.
